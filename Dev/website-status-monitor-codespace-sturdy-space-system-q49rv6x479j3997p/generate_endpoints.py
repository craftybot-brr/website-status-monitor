import json
import os
import sys

# Add the script's directory to the Python path to allow for relative imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def generate_azure_endpoints():
    """
    Parses the Azure Service Tags JSON file to extract storage endpoints for each region
    and generates a new endpoints.py file with the updated AZURE_ENDPOINTS dictionary.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    service_tags_path = os.path.join(script_dir, 'ServiceTags_Public_20250616.json')
    endpoints_path = os.path.join(script_dir, 'endpoints.py')

    try:
        with open(service_tags_path, 'r') as f:
            service_tags = json.load(f)
    except FileNotFoundError:
        print(f"Error: {service_tags_path} not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode {service_tags_path}.")
        return

    azure_endpoints = {}
    storage_tag_prefix = "Storage."

    for value in service_tags.get("values", []):
        service_name = value.get("name", "")
        if service_name.startswith(storage_tag_prefix):
            region = service_name[len(storage_tag_prefix):]
            if not region or "Global" in region:
                continue

            # Create a representative endpoint name
            endpoint_hostname = f"{region.lower().replace(' ', '')}.blob.core.windows.net"
            
            # Simple mapping to a broader region for grouping
            broad_region = "other"
            if any(sub in region for sub in ["US", "Canada", "Brazil"]):
                broad_region = "americas"
            elif any(sub in region for sub in ["Europe", "UK", "France", "Germany", "Switzerland", "Norway", "Sweden", "Poland", "Italy"]):
                broad_region = "europe"
            elif any(sub in region for sub in ["Asia", "Australia", "India", "Japan", "Korea"]):
                broad_region = "asia_pacific"
            elif any(sub in region for sub in ["Africa", "UAE", "Qatar", "Israel"]):
                broad_region = "middle_east_africa"

            if broad_region not in azure_endpoints:
                azure_endpoints[broad_region] = {
                    "name": f"{broad_region.replace('_', ' ').title()} Regions",
                    "endpoints": []
                }
            
            azure_endpoints[broad_region]["endpoints"].append({
                "name": region,
                "endpoint": endpoint_hostname,
                "region": region.lower(),
                "icon": "🇦🇿" 
            })

    # Fetch existing EC2_ENDPOINTS
    try:
        from endpoints import EC2_ENDPOINTS
    except (ImportError, SyntaxError):
        EC2_ENDPOINTS = {}

    # Write the new endpoints.py file
    with open(endpoints_path, 'w') as f:
        f.write("EC2_ENDPOINTS = " + json.dumps(EC2_ENDPOINTS, indent=4) + "\n\n")
        f.write("AZURE_ENDPOINTS = " + json.dumps(azure_endpoints, indent=4) + "\n")

    print(f"Successfully generated new {endpoints_path} file.")

if __name__ == "__main__":
    generate_azure_endpoints()
