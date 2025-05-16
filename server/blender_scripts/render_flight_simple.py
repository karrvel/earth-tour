#!/usr/bin/env python3
import bpy
import bmesh
import math
import os
import sys
import json
import argparse
import traceback
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

    # Set resolution based on quality (using 9:16 aspect ratio for mobile viewing)
    resolution = {
        '480p': (480, 854),    # 9:16 ratio of 480p
        '720p': (720, 1280),   # 9:16 ratio of 720p
        '1080p': (1080, 1920), # 9:16 ratio of 1080p
        '4k': (2160, 3840)     # 9:16 ratio of 4K
    }.get(quality.lower(), (720, 1280))

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

    # Set the render engine to Workbench for faster rendering
    scene.render.engine = 'BLENDER_WORKBENCH'

    # Configure workbench renderer for better appearance
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.show_shadows = True

    # Create world environment with a simple blue background
    world = bpy.data.worlds.new("Earth_World")
    world.use_nodes = True
    bg_node = world.node_tree.nodes["Background"]
    bg_node.inputs[0].default_value = (0.0, 0.0, 0.05, 1.0)  # Very dark blue for space
    bg_node.inputs[1].default_value = 1.0  # Strength
    scene.world = world  # Assign the world to the scene

    # Add better lighting setup
    # Main sun light
    sun = bpy.data.lights.new("Sun", type='SUN')
    sun.energy = 5.0
    sun_obj = bpy.data.objects.new("Sun", sun)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.location = (10, -10, 10)
    sun_obj.rotation_euler = (radians(45), radians(45), 0)

    # Add a rim light to highlight the Earth's edges
    rim_light = bpy.data.lights.new("RimLight", type='SUN')
    rim_light.energy = 2.0
    rim_light_obj = bpy.data.objects.new("RimLight", rim_light)
    bpy.context.collection.objects.link(rim_light_obj)
    rim_light_obj.location = (-10, 2, 5)
    rim_light_obj.rotation_euler = (radians(30), radians(-30), 0)

    # Add a fill light for better visibility
    fill_light = bpy.data.lights.new("FillLight", type='SUN')
    fill_light.energy = 1.0
    fill_light_obj = bpy.data.objects.new("FillLight", fill_light)
    bpy.context.collection.objects.link(fill_light_obj)
    fill_light_obj.location = (0, 5, -5)
    fill_light_obj.rotation_euler = (radians(-30), 0, 0)

    # Create Earth sphere
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0, location=(0, 0, 0))
    earth = bpy.context.view_layer.objects.active
    earth.name = "Earth"

    # Create better Earth materials
    # Create a UV sphere with higher resolution for better texture mapping
    checker = bmesh.new()
    bmesh.ops.create_uvsphere(checker, u_segments=32, v_segments=16, radius=1.0)
    checker.to_mesh(earth.data)
    checker.free()
    
    # Create Earth materials
    earth_mat = bpy.data.materials.new(name="Earth_Material")
    earth_mat.diffuse_color = (0.05, 0.3, 0.6, 1.0)  # Base blue color
    earth.data.materials.append(earth_mat)

    # Create land material with green color
    land_mat = bpy.data.materials.new(name="Land_Material")
    land_mat.diffuse_color = (0.1, 0.5, 0.1, 1.0)  # Green for land
    earth.data.materials.append(land_mat)

    # Enhanced Earth pattern - create continent shapes
    for i, face in enumerate(earth.data.polygons):
        # Create distinct continental regions
        x, y, z = face.center
        
        # Northern and Southern Americas
        if (-0.5 > x > -0.9) and (abs(z) < 0.7):
            face.material_index = 1  # Land
        # Africa and Europe
        elif (0.2 < x < 0.6) and (-0.2 < z < 0.7):
            face.material_index = 1  # Land
        # Asia
        elif (0.5 < x < 0.9) and (0.0 < z < 0.7):
            face.material_index = 1  # Land
        # Australia
        elif (0.7 < x < 0.9) and (-0.6 < z < -0.2):
            face.material_index = 1  # Land
        # Antarctica
        elif (abs(z) > 0.8):
            face.material_index = 1  # Land with snow cap

    # Create a plane to represent the aircraft
    bpy.ops.mesh.primitive_cone_add(radius1=0.05, radius2=0.0, depth=0.2, location=(0, 0, 0))
    plane = bpy.context.view_layer.objects.active
    plane.name = "Aircraft"

    # Create a material for the plane
    plane_mat = bpy.data.materials.new(name="Plane_Material")
    plane_mat.diffuse_color = (0.8, 0.0, 0.0, 1.0)  # Red for visibility
    plane.data.materials.append(plane_mat)

    # Create a material for the trail
    trail_mat = bpy.data.materials.new(name="Trail_Material")
    trail_mat.diffuse_color = (1.0, 1.0, 0.0, 1.0)  # Yellow for the trail

    # Add camera
    camera_data = bpy.data.cameras.new(name='Camera')
    camera = bpy.data.objects.new('Camera', camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera

    # Position camera initially to view the Earth
    camera.location = (0, -3, 2.5)
    camera.rotation_euler = (radians(65), 0, 0)
    camera_data.lens = 24  # Wider field of view for portrait orientation

    # Select the camera to make it active
    bpy.context.view_layer.objects.active = camera
    # Frame the Earth in the viewport (this doesn't affect rendering, but helps debugging)
    # The following line is commented out as it causes errors in background mode
    # if 'Earth' in bpy.data.objects:
    #     bpy.ops.view3d.view_selected(override={'selected_objects': [bpy.data.objects['Earth']]})

    # Helper function to convert lat/long to 3D coordinates
    def latlon_to_xyz(lat, lon, radius=1.0):
        lat_rad = radians(lat)
        lon_rad = radians(lon)
        x = radius * cos(lat_rad) * cos(lon_rad)
        y = radius * cos(lat_rad) * sin(lon_rad)
        z = radius * sin(lat_rad)
        return (x, y, z)

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
                # t = i / steps # t is not used here
                x = cos(start_lat_rad) * cos(start_lon_rad)
                y = cos(start_lat_rad) * sin(start_lon_rad)
                z = sin(start_lat_rad)
                points.append((x, y, z))
            return points

        # Calculate the value for asin safely
        a = sin((end_lat_rad - start_lat_rad) / 2) ** 2
        b = cos(start_lat_rad) * cos(end_lat_rad) * sin(d_lon / 2) ** 2
        sin_sigma_val = sqrt(a + b) # Renamed to avoid conflict with math.sin

        # Ensure we're in domain for asin
        sin_sigma_val = max(-1.0, min(sin_sigma_val, 1.0))
        d_sigma = 2 * asin(sin_sigma_val)

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
                A_val = sin((1 - t) * d_sigma) / sin(d_sigma) # Renamed A
                B_val = sin(t * d_sigma) / sin(d_sigma)       # Renamed B

                x = A_val * cos(start_lat_rad) * cos(start_lon_rad) + B_val * cos(end_lat_rad) * cos(end_lon_rad)
                y = A_val * cos(start_lat_rad) * sin(start_lon_rad) + B_val * cos(end_lat_rad) * sin(end_lon_rad)
                z = A_val * sin(start_lat_rad) + B_val * sin(end_lat_rad)

            # Normalize the vector to ensure it's on the unit sphere
            mag = sqrt(x**2 + y**2 + z**2)
            if mag == 0: # Avoid division by zero if points are identical and d_sigma was near zero
                x, y, z = cos(start_lat_rad) * cos(start_lon_rad), cos(start_lat_rad) * sin(start_lon_rad), sin(start_lat_rad)
            else:
                x, y, z = x/mag, y/mag, z/mag

            points.append((x, y, z))

        return points

    # Create waypoints from locations
    waypoints = []
    location_names = []
    for i, loc in enumerate(locations):
        lat = loc['lat']
        lon = loc['lon']
        waypoints.append((lat, lon))
        # Create a name for the location if not provided
        location_names.append(loc.get('name', f"Location {i+1}")) # Use provided name or default

    # Calculate frames per segment
    total_segments = len(waypoints) - 1
    frames_per_segment = frames // total_segments if total_segments > 0 else frames
    if frames_per_segment == 0 and total_segments > 0 : frames_per_segment = 1 # Ensure at least 1 frame per segment if there are segments

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
        label_text.align_y = 'CENTER' 

        label_obj = bpy.data.objects.new(f"Label{i}", label_text)
        bpy.context.collection.objects.link(label_obj)
        label_obj.location = pos + Vector((0, 0, 0.05)) 
        label_obj.rotation_euler = (radians(90), 0, 0) 
        labels.append(label_obj)

    # Create a curve object for the trail
    curve_data = bpy.data.curves.new('FlightTrail', type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 2
    curve_data.bevel_depth = 0.01  # Thickness of the trail
    trail_obj = bpy.data.objects.new("FlightTrail", curve_data)
    bpy.context.collection.objects.link(trail_obj)
    trail_obj.data.materials.append(trail_mat)
    
    if not curve_data.splines: 
        spline = curve_data.splines.new('POLY')
    else: 
        spline = curve_data.splines[0]
    
    if not spline.points:
        spline.points.add(1) 

    current_trail_point_index = 0
    for i in range(total_segments):
        start_lat, start_lon = waypoints[i]
        end_lat, end_lon = waypoints[i + 1]
        
        # Ensure steps is at least 0 for great_circle_points if frames_per_segment is 0 or 1
        num_gcp_steps = max(0, frames_per_segment - 1 if frames_per_segment > 0 else 0)
        path_points = great_circle_points(start_lat, start_lon, end_lat, end_lon, steps=num_gcp_steps)
        if not path_points: # Handle case where great_circle_points might return empty
            log(f"Warning: No path points generated for segment {i}", "WARNING")
            continue


        for j, point_coords in enumerate(path_points):
            frame_num = i * frames_per_segment + j + 1
            if frame_num > scene.frame_end: 
                continue
            bpy.context.scene.frame_set(frame_num)

            plane_pos = Vector(point_coords) * 1.02  
            plane.location = plane_pos
            plane.keyframe_insert(data_path="location", frame=frame_num)

            if i == 0 and j == 0: 
                spline.points[0].co = (plane_pos.x, plane_pos.y, plane_pos.z, 1)
                current_trail_point_index = 0 
            else:
                if current_trail_point_index < len(spline.points): # Check if index is valid
                    prev_point_co = spline.points[current_trail_point_index].co
                    if Vector((prev_point_co[0], prev_point_co[1], prev_point_co[2])).length > 0.0001 and \
                       (Vector((prev_point_co[0], prev_point_co[1], prev_point_co[2])) - plane_pos).length > 0.0001 :
                        spline.points.add(1)
                        current_trail_point_index += 1
                        spline.points[current_trail_point_index].co = (plane_pos.x, plane_pos.y, plane_pos.z, 1)
                    elif Vector((prev_point_co[0], prev_point_co[1], prev_point_co[2])).length < 0.0001 : # First point was placeholder
                        spline.points[current_trail_point_index].co = (plane_pos.x, plane_pos.y, plane_pos.z, 1)

                else: # Should not happen if logic is correct, but as a fallback
                    spline.points.add(1)
                    current_trail_point_index = len(spline.points) -1
                    spline.points[current_trail_point_index].co = (plane_pos.x, plane_pos.y, plane_pos.z, 1)


            if j < len(path_points) - 1:
                next_point_coords = path_points[j + 1]
                current_vec_point = Vector(point_coords)
                next_vec_point = Vector(next_point_coords)
                
                direction = (next_vec_point - current_vec_point)
                if direction.length > 0.0001:
                    direction.normalize()
                else: 
                    if 'previous_direction' in plane: # MODIFIED HERE
                        direction = Vector(plane['previous_direction']) # MODIFIED HERE
                    else:
                        direction = Vector((1,0,0)) 
                
                plane['previous_direction'] = tuple(direction) # MODIFIED HERE

                up_vector_obj = -current_vec_point.normalized() 
                
                if abs(direction.dot(up_vector_obj)) > 0.999: 
                    if 'previous_right_vector' in plane: # MODIFIED HERE
                        right_vector = Vector(plane['previous_right_vector']) # MODIFIED HERE
                    else: 
                        temp_ref = Vector((0,0,1)) if abs(up_vector_obj.z) < 0.9 else Vector((0,1,0))
                        right_vector = up_vector_obj.cross(temp_ref).normalized()
                    
                    forward_vector = up_vector_obj.cross(right_vector).normalized() 
                    if direction.dot(forward_vector) < 0: 
                        forward_vector = -forward_vector
                    direction = forward_vector 
                
                right_vector = up_vector_obj.cross(direction).normalized()
                true_forward = right_vector.cross(up_vector_obj).normalized()

                plane['previous_right_vector'] = tuple(right_vector) # MODIFIED HERE
                
                final_forward = true_forward
                final_up = up_vector_obj
                final_right = final_up.cross(final_forward)

                if final_right.length < 0.0001: 
                    if abs(final_up.z) < 0.9 : 
                        final_right = final_up.cross(Vector((0,0,1))).normalized()
                    else: 
                        final_right = final_up.cross(Vector((0,1,0))).normalized()
                    if final_right.length < 0.0001: # Ultimate fallback if still zero
                        final_right = Vector((1,0,0)) if abs(final_up.x) > 0.9 else Vector((0,1,0))


                final_forward = final_right.cross(final_up).normalized()
                if final_forward.length < 0.0001: # Fallback for forward
                    final_forward = direction # Use original direction if recalculation failed
                    # And re-calculate right and up if needed
                    final_right = final_up.cross(final_forward).normalized()
                    if final_right.length < 0.0001:
                         final_right = Vector((1,0,0)) if abs(final_up.x) > 0.9 else Vector((0,1,0)) # another fallback
                    final_up = final_forward.cross(final_right).normalized() # re-orthogonalize up



                rot_matrix = Matrix()
                rot_matrix[0].xyz = final_right
                rot_matrix[1].xyz = final_up
                rot_matrix[2].xyz = final_forward
                rot_matrix.transpose() 

                plane.matrix_world = Matrix.Translation(plane_pos) @ rot_matrix.to_4x4()
                plane.keyframe_insert(data_path="rotation_euler", frame=frame_num)
                # plane.keyframe_insert(data_path="location", frame=frame_num) # Location is already set and keyed

    # Animate labels
    for i, (lat, lon) in enumerate(waypoints):
        label = labels[i]
        base_appear_frame = i * frames_per_segment + 1
        
        # Visibility keyframes
        # Hidden before it appears
        if base_appear_frame > 1:
            label.hide_render = True
            label.keyframe_insert(data_path="hide_render", frame=base_appear_frame - 1)
            label.hide_viewport = True
            label.keyframe_insert(data_path="hide_viewport", frame=base_appear_frame - 1)

        # Visible when it appears
        label.hide_render = False
        label.keyframe_insert(data_path="hide_render", frame=base_appear_frame)
        label.hide_viewport = False
        label.keyframe_insert(data_path="hide_viewport", frame=base_appear_frame)

        # Hidden after its segment (unless it's the last label)
        if i < total_segments: # Not the last waypoint
            disappear_frame = (i + 1) * frames_per_segment
            if disappear_frame < frames: # Ensure it doesn't try to set keyframe beyond animation
                label.hide_render = True
                label.keyframe_insert(data_path="hide_render", frame=disappear_frame +1) # Disappears one frame after segment ends
                label.hide_viewport = True
                label.keyframe_insert(data_path="hide_viewport", frame=disappear_frame +1)
            else: # Stays visible if its segment goes to the end or beyond
                label.hide_render = False
                label.keyframe_insert(data_path="hide_render", frame=frames)
                label.hide_viewport = False
                label.keyframe_insert(data_path="hide_viewport", frame=frames)

        else: # Last label, stays visible until the end
            label.hide_render = False
            label.keyframe_insert(data_path="hide_render", frame=frames) # Ensure it's visible at the last frame
            label.hide_viewport = False
            label.keyframe_insert(data_path="hide_viewport", frame=frames)


    if not plane:
        log("Error: Aircraft object was not created.", "ERROR")
        sys.exit(1)

    for i in range(1, frames + 1):
        bpy.context.scene.frame_set(i)

        if plane:
            plane_pos_eval = plane.matrix_world.translation 
            direction_from_earth_center = plane_pos_eval.normalized()
            if direction_from_earth_center.length == 0: direction_from_earth_center = Vector((0,0,1)) # Fallback

            camera_height_offset = 0.8 
            camera.location = plane_pos_eval + direction_from_earth_center * camera_height_offset

            global_north_vec = Vector((0, 1, 0)) 
            projected_north = global_north_vec - global_north_vec.dot(direction_from_earth_center) * direction_from_earth_center
            if projected_north.length < 0.001: 
                projected_north = Vector((1,0,0)) - Vector((1,0,0)).dot(direction_from_earth_center) * direction_from_earth_center
                if projected_north.length < 0.001: 
                    projected_north = Vector((0,0,1)) - Vector((0,0,1)).dot(direction_from_earth_center) * direction_from_earth_center
                if projected_north.length < 0.001: # Ultimate fallback for projected_north
                    projected_north = Vector((0,1,0)) if direction_from_earth_center.z < 0.9 else Vector((1,0,0))


            cam_up_vector = projected_north.normalized()
            if cam_up_vector.length == 0: cam_up_vector = Vector((0,1,0)) # Fallback
            
            look_at_target = plane_pos_eval
            cam_forward_vector = (look_at_target - camera.location)
            if cam_forward_vector.length > 0.0001:
                cam_forward_vector.normalize()
            else: # Camera is at the target, look down or default
                cam_forward_vector = -direction_from_earth_center if direction_from_earth_center.length > 0 else Vector((0,0,-1))
            
            cam_z_axis = -cam_forward_vector 
            cam_x_axis = cam_up_vector.cross(cam_z_axis)
            if cam_x_axis.length > 0.0001:
                cam_x_axis.normalize()
            else: # up and z are parallel, choose arbitrary x
                cam_x_axis = cam_up_vector.cross(Vector((0,0,1)) if abs(cam_up_vector.z) < 0.9 else Vector((1,0,0))).normalized()


            cam_y_axis = cam_z_axis.cross(cam_x_axis).normalized() 
            if cam_y_axis.length == 0: # Fallback if z and x ended up parallel
                 cam_y_axis = Vector(cam_up_vector) # Use original up vector

            cam_rot_matrix = Matrix()
            cam_rot_matrix[0].xyz = cam_x_axis
            cam_rot_matrix[1].xyz = cam_y_axis
            cam_rot_matrix[2].xyz = cam_z_axis
            cam_rot_matrix.transpose() 

            camera.rotation_euler = cam_rot_matrix.to_euler('XYZ') 

            camera.keyframe_insert(data_path="location", frame=i)
            camera.keyframe_insert(data_path="rotation_euler", frame=i)

    scene.render.filepath = args.output
    log(f"Starting render to {args.output}")
    bpy.ops.render.render(animation=True, write_still=False)
    log(f"Rendering completed successfully to {args.output}")

except Exception as e:
    log(f"Error during rendering: {str(e)}", "ERROR")
    log(traceback.format_exc(), "ERROR")
    sys.exit(1)

log("Script completed successfully")
sys.exit(0)