import sys
from google.cloud import compute_v1
from google.api_core.exceptions import GoogleAPICallError
from google.auth import exceptions
from google.auth.credentials import Credentials
from google.auth.transport.requests import Request

def authenticate_with_service_account(credentials_dict):
    try:
        creds = Credentials.from_authorized_user_info(credentials_dict)
        
        # Check if the credentials have expired
        if not creds.valid:
            creds.refresh(Request())
        
        return creds
    except exceptions.GoogleAuthError as e:
        print(f"Error authenticating: {e}")
        return None

def create_disk_from_snapshot(project_id, zone, snapshot_name, new_disk_name):
    client = compute_v1.DisksClient()
    source_snapshot = f"projects/{project_id}/global/snapshots/{snapshot_name}"
    disk = compute_v1.Disk(name=new_disk_name, source_snapshot=source_snapshot)

    try:
        operation = client.insert(project=project_id, zone=zone, disk_resource=disk)
        operation.result()
        print(f"Disk '{new_disk_name}' created successfully from snapshot.")
    except GoogleAPICallError as e:
        print(f"Error creating disk '{new_disk_name}' from snapshot: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while creating disk '{new_disk_name}' from snapshot: {e}")
        sys.exit(1)

def create_snapshot(project_id, zone, disk_name, snapshot_name):
    client = compute_v1.SnapshotsClient()
    source_disk = f"projects/{project_id}/zones/{zone}/disks/{disk_name}"
    snapshot = compute_v1.Snapshot(name=snapshot_name, source_disk=source_disk)

    try:
        operation = client.insert(project=project_id, snapshot_resource=snapshot)
        operation.result()
        print(f"Snapshot '{snapshot_name}' created successfully.")
    except GoogleAPICallError as e:
        print(f"Error creating snapshot '{snapshot_name}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while creating snapshot '{snapshot_name}': {e}")
        sys.exit(1)

def create_vm_with_attached_disk(project_id, zone, vm_name, boot_disk_name, additional_disk_name, machine_type):
    client = compute_v1.InstancesClient()

    instance_resource = compute_v1.Instance(name=vm_name)

    # Define the image project and image family for Ubuntu 20.04 LTS
    image_project = "ubuntu-os-cloud"
    image_family = "ubuntu-2004-focal-v20230724"

    # Create the boot disk attachment using the Ubuntu image
    boot_disk = compute_v1.AttachedDisk(
        boot=True,
        auto_delete=True,
        initialize_params=compute_v1.AttachedDiskInitializeParams(
            disk_size_gb=10,
            source_image=f"projects/{image_project}/global/images/{image_family}",
        ),
    )

    # Create the additional disk attachment
    additional_disk = compute_v1.AttachedDisk(
        source=f"projects/{project_id}/zones/{zone}/disks/{additional_disk_name}",
        auto_delete=True,
    )

    instance_resource.disks = [boot_disk, additional_disk]

    instance_resource.machine_type = f"projects/{project_id}/zones/{zone}/machineTypes/{machine_type}"
    instance_resource.network_interfaces = [{"network": "global/networks/default"}]

    try:
        operation = client.insert(project=project_id, zone=zone, instance_resource=instance_resource)
        operation.result()
        print(f"VM '{vm_name}' created successfully with attached disk.")
    except GoogleAPICallError as e:
        print(f"Error creating VM '{vm_name}' with attached disk: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while creating VM '{vm_name}' with attached disk: {e}")
        sys.exit(1)

def delete_vm(project_id, zone, vm_name):
    client = compute_v1.InstancesClient()

    try:
        operation = client.delete(project=project_id, zone=zone, instance=vm_name)
        operation.result()
        print(f"VM '{vm_name}' deleted successfully.")
    except Exception as e:
        print(f"Error deleting VM '{vm_name}': {e}")

def delete_disk(project_id, zone, disk_name):
    client = compute_v1.DisksClient()

    try:
        disk_path = f"projects/{project_id}/zones/{zone}/disks/{disk_name}"
        operation = client.delete(project=project_id, zone=zone, disk=disk_name)
        operation.result()
        print(f"Disk '{disk_name}' at '{disk_path}' deleted successfully.")
    except Exception as e:
        print(f"Error deleting disk '{disk_name}': {e}")

def main():
    project_id = "qwiklabs-gcp-01-9b3d01cf03e9"
    zone = "us-central1-a"
    new_disk_name = "new-disk-from-snapshot"
    vm_name = "test-vm"
    disk_name = "unattached-disk"

    service_account_credentials = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "your-private-key-id",
        "private_key": "your-private-key",
        "client_email": "your-client-email",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://accounts.google.com/o/oauth2/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "your-client-x509-cert-url"
    }

    authenticated_creds = authenticate_with_service_account(service_account_credentials)

    if authenticated_creds:
        print("Authentication successful!")
    else:
        print("Authentication failed.")
        sys.exit(1)

    snapshot_name = f"{disk_name}-snapshot"

    print(f" - {disk_name}")
    create_snapshot(project_id, zone, disk_name, snapshot_name)
    print(f"   Created snapshot: {snapshot_name}")

    create_disk_from_snapshot(project_id, zone, snapshot_name, new_disk_name)
    print(f"   Created disk from snapshot: {new_disk_name}")

    create_vm_with_attached_disk(project_id, zone, vm_name, "new-boot-disk", new_disk_name, "e2-micro")

    print(f"   Created VM with attached disk: {vm_name}")
    print(f"   Start deleting VM: {vm_name}")
    delete_vm(project_id, zone, vm_name)

    # Uncomment this section if you want to delete the disk as well
    # print(f"   Start deleting disk: {new_disk_name}")
    # delete_disk(project_id, zone, new_disk_name)

if __name__ == "__main__":
    main()
    
