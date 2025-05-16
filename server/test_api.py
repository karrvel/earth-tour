import requests
import json
import time
import argparse

def main():
    parser = argparse.ArgumentParser(description='Test the Earth Tour Server API')
    parser.add_argument('--host', type=str, default='http://localhost:8000', 
                      help='API host URL')
    args = parser.parse_args()
    
    # Test locations
    test_data = {
        "locations": [
            {"name": "New York"},
            {"name": "London"},
            {"name": "Tokyo"},
            {"name": "Sydney"},
        ],
        "quality": "720p"  # Using 4K resolution for better quality
    }
    
    print(f"Testing Earth Tour Server API at {args.host}")
    
    # Test root endpoint
    try:
        response = requests.get(f"{args.host}/")
        if response.status_code == 200:
            print(f"✅ Root endpoint: {response.json()}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Failed to connect to the server: {str(e)}")
        return
    
    # Submit animation request
    try:
        response = requests.post(f"{args.host}/generate-animation", json=test_data)
        if response.status_code == 200:
            result = response.json()
            job_id = result.get("job_id")
            print(f"✅ Animation request submitted - Job ID: {job_id}")
            
            # Poll job status
            max_attempts = 60  # Maximum number of status checks
            for i in range(max_attempts):
                job_response = requests.get(f"{args.host}/job/{job_id}")
                job_status = job_response.json()
                status = job_status.get("status")
                
                print(f"Job status: {status} (attempt {i+1}/{max_attempts})")
                
                if status == "completed":
                    print(f"✅ Animation completed!")
                    print(f"Video URL: {args.host}{job_status.get('video_path')}")
                    print(f"Rendering duration: {job_status.get('duration', 'N/A')} seconds")
                    break
                elif status == "failed":
                    print(f"❌ Animation failed: {job_status.get('error', 'Unknown error')}")
                    break
                
                # Wait before next check
                time.sleep(5)
            else:
                print("❌ Job polling timed out")
        else:
            print(f"❌ Animation request failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error during request: {str(e)}")

if __name__ == "__main__":
    main()
