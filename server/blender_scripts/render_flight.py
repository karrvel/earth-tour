#!/usr/bin/env python3
import bpy
import bmesh
import math
import os
import sys
import json
import argparse
from math import radians, sin, cos, asin, sqrt, atan2
from mathutils import Vector, Matrix

# Setup basic logging (prints to Blender's console)
def log(message, level="INFO"):
    print(f"[{level}] {message}")
    sys.stdout.flush()  # Ensure output is immediately visible
log("Starting Blender flight path animation script")

# Parse command line arguments
try:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    
    parser = argparse.ArgumentParser(description="Render flight path animation")
    parser.add_argument("--config", required=True, help="Path to configuration JSON file")
    parser.add_argument("--output", required=True, help="Output video file path")
    args = parser.parse_args(argv)
    
    log(f"Parsed command line arguments: {argv}")
    log(f"Config file: {args.config}")
    log(f"Output file: {args.output}")
    
    # Load configuration from file
    with open(args.config, 'r') as f:
        config = json.load(f)
    log(f"Loaded configuration: {config}")
    
    # Extract parameters from config
    locations = config['locations']
    quality = config['quality']
    fps = config.get('fps', 30)
    
    # Always use the duration value provided in the config
    duration = config['duration']
    
    log(f"Rendering with: {len(locations)} locations, {quality} quality, {fps} fps, {duration}s duration")
    
    # Set resolution based on quality
    resolution = {
        '480p': (854, 480),
        '720p': (1280, 720),
        '1080p': (1920, 1080),
        '4k': (3840, 2160)
    }.get(quality, (1280, 720))
    
    log(f"Resolution: {resolution[0]}x{resolution[1]}, Total frames: {fps * duration}")
    
    # Calculate total frames
    frames = fps * duration
    
    # Clear existing scene
    log("Clearing existing scene")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Create a new scene
    log("Setting up scene and render settings")
    scene = bpy.context.scene
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    scene.render.fps = fps
    scene.frame_start = 1
    scene.frame_end = frames
    
    # Set the render engine to a reliable option with better appearance and speed
    scene.render.engine = 'BLENDER_WORKBENCH'  # Use Workbench for faster rendering in Blender 4.4.3
    
    # Configure workbench renderer for better appearance
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_shadows = True
    
    # Create world environment with a simple blue background and stars
    world = bpy.data.worlds.new("Earth_World")
    world.use_nodes = True
    bg_node = world.node_tree.nodes["Background"]
    bg_node.inputs[0].default_value = (0.0, 0.0, 0.05, 1.0)  # Very dark blue for space
    bg_node.inputs[1].default_value = 1.0  # Strength
    scene.world = world  # Assign the world to the scene
    
    # Add more lighting for better visibility
    # Add a rim light to highlight the Earth's edges
    sun = bpy.data.lights.new("Sun", type='SUN')
    sun.energy = 5.0
    sun_obj = bpy.data.objects.new("Sun", sun)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.location = (10, -10, 10)
    sun_obj.rotation_euler = (radians(45), radians(45), 0)
    
    rim_light = bpy.data.lights.new("RimLight", type='SUN')
    rim_light.energy = 2.0
    rim_light_obj = bpy.data.objects.new("RimLight", rim_light)
    bpy.context.collection.objects.link(rim_light_obj)
    rim_light_obj.location = (-10, 2, 5)
    rim_light_obj.rotation_euler = (radians(30), radians(-30), 0)

    # Create Earth sphere
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0, location=(0, 0, 0))
    # Make sure we get the active object properly in both GUI and headless mode
    earth = bpy.context.view_layer.objects.active
    if not earth:
        # Fallback to finding the object by name
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                earth = obj
                break
    earth.name = "Earth"
    log(f"Created Earth object: {earth.name}")

    # Create simple Earth materials for Workbench renderer
    # Create blue material for oceans
    ocean_mat = bpy.data.materials.new(name="Ocean_Material")
    ocean_mat.diffuse_color = (0.03, 0.15, 0.4, 1.0)  # Deep blue for oceans
    
    # Create green material for land
    land_mat = bpy.data.materials.new(name="Land_Material")
    land_mat.diffuse_color = (0.15, 0.5, 0.15, 1.0)  # Green for land
    
    # Create a simple material for the plane
    plane_mat = bpy.data.materials.new(name="Plane_Material")
    plane_mat.diffuse_color = (0.8, 0.0, 0.0, 1.0)  # Red for visibility
    
    # Assign material to Earth
    if earth.data.materials:
        earth.data.materials[0] = ocean_mat
    else:
        earth.data.materials.append(ocean_mat)
    
    # Add atmosphere glow - simplified for Workbench renderer
    atmosphere = bpy.data.materials.new(name="Atmosphere")
    atmosphere.diffuse_color = (0.1, 0.2, 0.8, 0.5)  # Blue glow with transparency

    # Create atmosphere sphere slightly larger than Earth
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.05, location=(0, 0, 0))
    # Make sure we get the active object properly in both GUI and headless mode
    atm = bpy.context.view_layer.objects.active
    if not atm or atm.name == "Earth":  # Make sure we don't get the Earth object
        # Fallback to finding the object by name or the last created object
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj != earth:
                atm = obj
                break
    atm.name = "Atmosphere"
    log(f"Created Atmosphere object: {atm.name}")
    
    # Assign atmosphere material
    if atm.data.materials:
        atm.data.materials[0] = atmosphere
    else:
        atm.data.materials.append(atmosphere)

    # Make atmosphere partially transparent
    # Updated for Blender 4.4+ compatibility
    atmosphere.blend_method = 'BLEND'
    
    # Add camera
    camera_data = bpy.data.cameras.new(name='Camera')
    camera = bpy.data.objects.new('Camera', camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    
    # Position camera to view Earth
    camera.location = (0, -3, 1.5)  # Position camera to view Earth
    camera.rotation_euler = (radians(60), 0, 0)  # Rotate camera to look at Earth
    camera_data.lens = 35  # Set lens for a good field of view
    
    # Helper function to convert lat/long to 3D coordinates
    def latlon_to_xyz(lat, lon, radius=1.0):
        lat_rad = radians(lat)
        lon_rad = radians(lon)
        x = radius * cos(lat_rad) * cos(lon_rad)
        y = radius * cos(lat_rad) * sin(lon_rad)
        z = radius * sin(lat_rad)
        return (x, y, z)

    # Create a plane to represent the aircraft
    bpy.ops.mesh.primitive_cone_add(radius1=0.05, radius2=0.0, depth=0.2, location=(0, 0, 0))
    # Make sure we get the active object properly in both GUI and headless mode
    plane = bpy.context.view_layer.objects.active
    if not plane or plane.name in ["Earth", "Atmosphere"]:
        # Fallback to finding the object by name or the last created object
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj != earth and obj != atm:
                plane = obj
                break
    plane.name = "Aircraft"
    log(f"Created Aircraft object: {plane.name}")
    
    # Rotate to point along Y axis
    plane.rotation_euler = (0, radians(90), 0)
    
    # Assign plane material
    if plane.data.materials:
        plane.data.materials[0] = plane_mat
    else:
        plane.data.materials.append(plane_mat)

    # Helper function for great circle path calculation
    def great_circle_points(start_lat, start_lon, end_lat, end_lon, steps=100):
        log(f"Calculating great circle: {start_lat},{start_lon} to {end_lat},{end_lon}")
        
        # Convert to radians
        start_lat_rad = radians(start_lat)
        start_lon_rad = radians(start_lon)
        end_lat_rad = radians(end_lat)
        end_lon_rad = radians(end_lon)
        
        # Calculate the angular distance
        d_lon = end_lon_rad - start_lon_rad
        
        # Handle edge case: same point
        if abs(end_lat_rad - start_lat_rad) < 1e-10 and abs(d_lon) < 1e-10:
            # Linear interpolation for identical points
            log("Points are nearly identical, using linear interpolation", "WARNING")
            points = []
            for i in range(steps + 1):
                t = i / steps
                x = cos(start_lat_rad) * cos(start_lon_rad)
                y = cos(start_lat_rad) * sin(start_lon_rad)
                z = sin(start_lat_rad)
                points.append((x, y, z))
            return points
        
        # Use safer haversine formula
        a = sin((end_lat_rad - start_lat_rad) / 2) ** 2
        b = cos(start_lat_rad) * cos(end_lat_rad) * sin(d_lon / 2) ** 2
        sin_sigma = sqrt(a + b)
        
        # Clamp to valid range to avoid domain errors
        sin_sigma = max(-1.0, min(sin_sigma, 1.0))
        d_sigma = 2 * asin(sin_sigma)
        
        log(f"Great circle distance: {d_sigma} radians")
        
        # Generate points along the great circle
        points = []
        for i in range(steps + 1):
            t = i / steps
            
            # Handle edge case: very small distance
            if abs(d_sigma) < 1e-10:
                x = cos(start_lat_rad) * cos(start_lon_rad)
                y = cos(start_lat_rad) * sin(start_lon_rad)
                z = sin(start_lat_rad)
            else:
                # Standard spherical interpolation
                A = sin((1 - t) * d_sigma) / sin(d_sigma)
                B = sin(t * d_sigma) / sin(d_sigma)
                
                x = A * cos(start_lat_rad) * cos(start_lon_rad) + B * cos(end_lat_rad) * cos(end_lon_rad)
                y = A * cos(start_lat_rad) * sin(start_lon_rad) + B * cos(end_lat_rad) * sin(end_lon_rad)
                z = A * sin(start_lat_rad) + B * sin(end_lat_rad)
            
            # Normalize to ensure we're on the unit sphere
            mag = sqrt(x**2 + y**2 + z**2)
            x, y, z = x/mag, y/mag, z/mag
            points.append((x, y, z))
        
        return points

    # Create waypoints from locations
    waypoints = []
    for loc in locations:
        lat = loc['lat']
        lon = loc['lon']
        waypoints.append((lat, lon))
    
    # Animate plane along the flight path
    total_segments = len(waypoints) - 1
    frames_per_segment = frames // total_segments
    
    for i in range(total_segments):
        start_lat, start_lon = waypoints[i]
        end_lat, end_lon = waypoints[i + 1]
        
        # Calculate path points for this segment
        path_points = great_circle_points(start_lat, start_lon, end_lat, end_lon, steps=frames_per_segment)
        
        # Animate plane along path
        for j, point in enumerate(path_points):
            frame_num = i * frames_per_segment + j + 1
            bpy.context.scene.frame_set(frame_num)
            
            # Position plane slightly above Earth's surface
            plane.location = Vector(point) * 1.02
            plane.keyframe_insert(data_path="location", frame=frame_num)
            
            # Orient plane along path direction
            if j < len(path_points) - 1:
                next_point = Vector(path_points[j + 1])
                direction = (next_point - Vector(point)).normalized()
                up = -Vector(point).normalized()  # Up is away from Earth center
                forward = direction
                right = forward.cross(up)
                up = right.cross(forward)  # Recalculate for orthogonality
                
                # Create rotation matrix and apply to plane
                rot_matrix = Matrix((right, forward, up)).transposed().to_4x4()
                plane.matrix_world = rot_matrix
                plane.matrix_world.translation = Vector(point) * 1.02
                plane.keyframe_insert(data_path="rotation_euler", frame=frame_num)
    
    # Animate labels to appear when the plane reaches each waypoint
    for i, (lat, lon) in enumerate(waypoints):
        # Convert lat/lon to 3D position
        pos = Vector(latlon_to_xyz(lat, lon, 1.02))
        
        # Get the frame where the plane reaches this waypoint
        if i == 0:
            appear_frame = 1
        else:
            appear_frame = i * frames_per_segment + 1
        
        # Make the label appear when the plane reaches this waypoint
        label = labels[i]
        
        # Hide the label initially
        if i > 0:  # Keep the first label visible from the start
            label.hide_render = True
            label.hide_viewport = True
            label.keyframe_insert(data_path="hide_render", frame=1)
            label.keyframe_insert(data_path="hide_viewport", frame=1)
        
        # Make the label appear
        label.hide_render = False
        label.hide_viewport = False
        label.keyframe_insert(data_path="hide_render", frame=appear_frame)
        label.keyframe_insert(data_path="hide_viewport", frame=appear_frame)
    
    # Animate camera to follow the plane while keeping Earth in view
    for i in range(1, frames + 1):
        bpy.context.scene.frame_set(i)
        
        # Get plane position at this frame
        plane_pos = Vector(plane.location)
        earth_center = Vector((0, 0, 0))
        
        # Position camera to see both plane and Earth
        camera_distance = (plane_pos - earth_center).magnitude * 1.5
        camera_direction = (plane_pos - earth_center).normalized()
        camera.location = earth_center - camera_direction * camera_distance
        
        # Make camera look at the plane
        direction_to_plane = (plane_pos - camera.location).normalized()
        rotation_quat = direction_to_plane.to_track_quat('-Z', 'Y')
        camera.rotation_euler = rotation_quat.to_euler()
        
        # Set keyframes for camera
        camera.keyframe_insert(data_path="location", frame=i)
        camera.keyframe_insert(data_path="rotation_euler", frame=i)
    
    # Adjust camera lens for better view
    camera.data.lens = 20
    
    # Set output path
    scene.render.filepath = args.output
    
    # Render animation
    log(f"Starting render to {args.output}")
    bpy.ops.render.render(animation=True, write_still=False)
    
    log(f"Rendering completed successfully to {args.output}")
    sys.exit(0)  # Exit with success code
except Exception as e:
    log(f"Error during rendering: {str(e)}", "ERROR")
    import traceback
    log(f"Traceback: {traceback.format_exc()}", "ERROR")
    sys.exit(1)  # Exit with error code

    # Create a new scene
    log("Setting up scene and render settings")
    scene = bpy.context.scene
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    scene.render.fps = fps
    scene.frame_start = 1
    scene.frame_end = frames
    
    # Set the render engine to a reliable option with better appearance and speed
    scene.render.engine = 'BLENDER_WORKBENCH'  # Use Workbench for faster rendering in Blender 4.4.3
    
    # Configure workbench renderer for better appearance
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_shadows = True
    
    # Create world environment with a simple blue background and stars
    world = bpy.data.worlds.new("Earth_World")
    world.use_nodes = True
    bg_node = world.node_tree.nodes["Background"]
    bg_node.inputs[0].default_value = (0.0, 0.0, 0.05, 1.0)  # Very dark blue for space
    bg_node.inputs[1].default_value = 1.0  # Strength
    scene.world = world  # Assign the world to the scene
    
    # Add more lighting for better visibility
    # Add a rim light to highlight the Earth's edges
    rim_light = bpy.data.lights.new("RimLight", type='SUN')
    rim_light.energy = 2.0
    rim_light_obj = bpy.data.objects.new("RimLight", rim_light)
    bpy.context.collection.objects.link(rim_light_obj)
    rim_light_obj.location = (-10, 2, 5)
    rim_light_obj.rotation_euler = (radians(30), radians(-30), 0)

    # Create Earth sphere
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0, location=(0, 0, 0))
    # Make sure we get the active object properly in both GUI and headless mode
    earth = bpy.context.view_layer.objects.active
    if not earth:
        # Fallback to finding the object by name
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                earth = obj
                break
    earth.name = "Earth"
    log(f"Created Earth object: {earth.name}")

    # Create simple Earth materials for Workbench renderer
    # Create blue material for oceans
    ocean_mat = bpy.data.materials.new(name="Ocean_Material")
    ocean_mat.diffuse_color = (0.03, 0.15, 0.4, 1.0)  # Deep blue for oceans
    
    # Create green material for land
    land_mat = bpy.data.materials.new(name="Land_Material")
    land_mat.diffuse_color = (0.15, 0.5, 0.15, 1.0)  # Green for land
    
    # Create a simple material for the plane
    plane_mat = bpy.data.materials.new(name="Plane_Material")
    plane_mat.diffuse_color = (0.8, 0.0, 0.0, 1.0)  # Red for visibility
    
    # Assign material to Earth
    if earth.data.materials:
        earth.data.materials[0] = ocean_mat
    else:
        earth.data.materials.append(ocean_mat)
    
    # Add atmosphere glow - simplified for Workbench renderer
    atmosphere = bpy.data.materials.new(name="Atmosphere")
    atmosphere.diffuse_color = (0.1, 0.2, 0.8, 0.5)  # Blue glow with transparency

    # Create atmosphere sphere slightly larger than Earth
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.05, location=(0, 0, 0))
    # Make sure we get the active object properly in both GUI and headless mode
    atm = bpy.context.view_layer.objects.active
    if not atm or atm.name == "Earth":  # Make sure we don't get the Earth object
        # Fallback to finding the object by name or the last created object
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj != earth:
                atm = obj
                break
    atm.name = "Atmosphere"
    log(f"Created Atmosphere object: {atm.name}")
    
    # Assign atmosphere material
    if atm.data.materials:
        atm.data.materials[0] = atmosphere
    else:
        atm.data.materials.append(atmosphere)

    # Make atmosphere partially transparent
    # Updated for Blender 4.4+ compatibility
    atmosphere.blend_method = 'BLEND'

    # Add lighting
    sun = bpy.data.lights.new("Sun", type='SUN')
    sun.energy = 5.0
    sun_obj = bpy.data.objects.new("Sun", sun)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.location = (10, -10, 10)
    sun_obj.rotation_euler = (radians(45), radians(45), 0)

    # Add camera
    camera_data = bpy.data.cameras.new(name='Camera')
    camera = bpy.data.objects.new('Camera', camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera

    # Position camera
    camera.location = (0, -5, 2)
    camera.rotation_euler = (radians(75), 0, 0)
    camera_data.lens = 35

    # Helper function to convert lat/long to 3D coordinates
    def latlon_to_xyz(lat, lon, radius=1.0):
        lat_rad = radians(lat)
        lon_rad = radians(lon)
        x = radius * cos(lat_rad) * cos(lon_rad)
        y = radius * cos(lat_rad) * sin(lon_rad)
        z = radius * sin(lat_rad)
        return (x, y, z)

    # Create a plane to represent the aircraft
    bpy.ops.mesh.primitive_cone_add(radius1=0.05, radius2=0.0, depth=0.2, location=(0, 0, 0))
    # Make sure we get the active object properly in both GUI and headless mode
    plane = bpy.context.view_layer.objects.active
    if not plane or plane.name in ["Earth", "Atmosphere"]:
        # Fallback to finding the object by name or the last created object
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj != earth and obj != atm:
                plane = obj
                break
    plane.name = "Aircraft"
    log(f"Created Aircraft object: {plane.name}")
    
    # Rotate to point along Y axis
    plane.rotation_euler = (0, radians(90), 0)
    
    # Assign plane material
    if plane.data.materials:
        plane.data.materials[0] = plane_mat
    # We already assigned the material above

    # Helper function for great circle path calculation
    def great_circle_points(start_lat, start_lon, end_lat, end_lon, steps=100):
        log(f"Calculating great circle: {start_lat},{start_lon} to {end_lat},{end_lon}")
        
        # Convert to radians
        start_lat_rad = radians(start_lat)
        start_lon_rad = radians(start_lon)
        end_lat_rad = radians(end_lat)
        end_lon_rad = radians(end_lon)
        
        # Use safer haversine formula
        d_lon = end_lon_rad - start_lon_rad
        
        # Check if points are nearly identical
        if abs(end_lat_rad - start_lat_rad) < 1e-10 and abs(d_lon) < 1e-10:
            log("Points are nearly identical, using linear interpolation", "WARNING")
            # Just do linear interpolation for nearly identical points
            points = []
            for i in range(steps + 1):
                t = i / steps
                x = cos(start_lat_rad) * cos(start_lon_rad)
                y = cos(start_lat_rad) * sin(start_lon_rad)
                z = sin(start_lat_rad)
                points.append((x, y, z))
            return points
            
        # Calculate the value for asin safely
        a = sin((end_lat_rad - start_lat_rad) / 2) ** 2
        b = cos(start_lat_rad) * cos(end_lat_rad) * sin(d_lon / 2) ** 2
        sin_sigma = sqrt(a + b)
        
        # Ensure we're in domain for asin
        sin_sigma = max(-1.0, min(sin_sigma, 1.0))
        d_sigma = 2 * asin(sin_sigma)
        
        log(f"Great circle distance: {d_sigma} radians")
        
        points = []
        for i in range(steps + 1):
            t = i / steps
            
            # Special case for nearly zero angle
            if abs(d_sigma) < 1e-10:
                # Linear interpolation
                x = cos(start_lat_rad) * cos(start_lon_rad)
                y = cos(start_lat_rad) * sin(start_lon_rad)
                z = sin(start_lat_rad)
            else:
                # Calculate intermediate point at t on the great circle
                A = sin((1 - t) * d_sigma) / sin(d_sigma)
                B = sin(t * d_sigma) / sin(d_sigma)
                
                x = A * cos(start_lat_rad) * cos(start_lon_rad) + B * cos(end_lat_rad) * cos(end_lon_rad)
                y = A * cos(start_lat_rad) * sin(start_lon_rad) + B * cos(end_lat_rad) * sin(end_lon_rad)
                z = A * sin(start_lat_rad) + B * sin(end_lat_rad)
            
            # Normalize the vector to ensure it's on the unit sphere
            mag = sqrt(x**2 + y**2 + z**2)
            x, y, z = x/mag, y/mag, z/mag
            
            # Convert to Cartesian coordinates (already done)
            points.append((x, y, z))
        
        return points

    # Create waypoints from locations
    waypoints = []
    for loc in locations:
        lat = loc['lat']
        lon = loc['lon']
        waypoints.append((lat, lon))

    # Calculate frames per segment
    total_segments = len(waypoints) - 1
    frames_per_segment = frames // total_segments
    
    # Create location labels
    labels = []
    for i, (lat, lon) in enumerate(waypoints):
        # Convert lat/lon to 3D position
        pos = Vector(latlon_to_xyz(lat, lon, 1.02))  # Slightly above Earth surface
        
        # Create text object for the label
        label_text = bpy.data.curves.new(type="FONT", name=f"LabelText{i}")
        label_text.body = location_names[i]
        label_text.size = 0.05
        label_text.align_x = 'CENTER'
        
        # Create the text object
        label_obj = bpy.data.objects.new(f"Label{i}", label_text)
        bpy.context.collection.objects.link(label_obj)
        
        # Position the label above the location point
        label_obj.location = pos + Vector((0, 0, 0.1))
        
        # Make the label face the camera
        label_obj.rotation_euler = (radians(90), 0, 0)
        
        # Store the label object for animation
        labels.append(label_obj)
    
    # Create a curve object for the trail
    curve_data = bpy.data.curves.new('FlightTrail', type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 2
    curve_data.bevel_depth = 0.01  # Thickness of the trail
    
    # Create the trail object
    trail_obj = bpy.data.objects.new("FlightTrail", curve_data)
    bpy.context.collection.objects.link(trail_obj)
    
    # Assign the yellow material to the trail
    if trail_obj.data.materials:
        trail_obj.data.materials[0] = trail_mat
    else:
        trail_obj.data.materials.append(trail_mat)
    
    # Create flight path and animate plane
    for i in range(total_segments):
        start_lat, start_lon = waypoints[i]
        end_lat, end_lon = waypoints[i + 1]
        
        # Get great circle points between waypoints
        path_points = great_circle_points(start_lat, start_lon, end_lat, end_lon, steps=frames_per_segment)
        
        # Animate plane position along path
        for j, point in enumerate(path_points):
            frame_num = i * frames_per_segment + j + 1
            bpy.context.scene.frame_set(frame_num)
            
            # Set plane position
            plane_pos = Vector(point) * 1.02  # Slightly above Earth's surface
            plane.location = plane_pos
            plane.keyframe_insert(data_path="location", frame=frame_num)
            
            # Update the trail curve at each frame
            if j == 0 and i == 0:
                # Create the first point of the trail
                spline = curve_data.splines.new('POLY')
                spline.points.add(1)
                spline.points[0].co = (plane_pos.x, plane_pos.y, plane_pos.z, 1)
                spline.points[1].co = (plane_pos.x, plane_pos.y, plane_pos.z, 1)
            else:
                # Add a new point to the trail
                spline = curve_data.splines[0]
                spline.points.add(1)
                spline.points[-1].co = (plane_pos.x, plane_pos.y, plane_pos.z, 1)
            
            # Animate the trail visibility
            trail_obj.keyframe_insert(data_path="hide_render", frame=frame_num)
            trail_obj.keyframe_insert(data_path="hide_viewport", frame=frame_num)
            
            # Calculate plane orientation
            if j < len(path_points) - 1:
                # Look-at the next point
                next_point = Vector(path_points[j + 1])
                direction = (next_point - Vector(point)).normalized()
                
                # Up vector is toward the center of the Earth (normalized location)
                up = -Vector(point).normalized()
                
                # Calculate rotation to align with flight direction
                forward = direction
                right = forward.cross(up)
                up = right.cross(forward)
                
                # Create rotation matrix
                rot_matrix = Matrix((right, forward, up)).transposed().to_4x4()
                plane.matrix_world = rot_matrix
                plane.matrix_world.translation = Vector(point) * 1.02
                
                # Insert keyframe
                plane.keyframe_insert(data_path="rotation_euler", frame=frame_num)

    # Orbit camera around the Earth to follow the plane
    # Position camera to get a wider view
    for i in range(1, frames + 1):
        bpy.context.scene.frame_set(i)
        
        # Get current plane position
        plane_pos = Vector(plane.location)
        
        # Calculate more distant camera position to see more of the Earth
        # Start further back for a better view
        camera_offset = Vector((-2.0, -2.0, 1.0))  # Further away for a better view
        camera.location = plane_pos + camera_offset
        
        # Look at the plane
        direction = (plane_pos - camera.location).normalized()
        
        # Set camera rotation to look at plane
        camera.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
        
        # Insert keyframe
        camera.keyframe_insert(data_path="location", frame=i)
        camera.keyframe_insert(data_path="rotation_euler", frame=i)
    
    # Set camera lens for wider view
    camera.data.lens = 20  # Wider angle lens

    # Set render output path
    scene.render.filepath = args.output
    log(f"Setting render output path to: {args.output}")
    
    # Ensure the output directory exists
    output_dir = os.path.dirname(args.output)
    os.makedirs(output_dir, exist_ok=True)
    
    # Render animation
    log("Starting render process")
    bpy.ops.render.render(animation=True, write_still=False)
    
    log(f"Animation rendered to {args.output}")
    
    # Verify the output file exists
    if os.path.exists(args.output):
        log(f"Output file successfully created at: {args.output}")
        file_size = os.path.getsize(args.output)
        log(f"File size: {file_size} bytes")
    else:
        log(f"Output file was not created at: {args.output}", "ERROR")
    
except Exception as e:
    log(f"Error during rendering: {str(e)}", "ERROR")
    log(traceback.format_exc(), "ERROR")
    sys.exit(1)

log("Script completed successfully")
sys.exit(0)
