import modal
import re
import os
import shutil

app = modal.App("download-storage-app")
output = modal.Volume.from_name("comfyui-outputs", create_if_missing=True)
zipoutput = modal.Volume.from_name("zip-outputs", create_if_missing=True)
zippath = '/usr/zip/output'
zipextension = 'zip'

@app.function(volumes={
        "/usr/zip" : zipoutput,
    })
def download_regex_matches(volume_name, pattern, local_dir="./downloads"):
    
    # 2. Create local directory if it doesn't exist
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    # 3. List all files and apply regex
    regex = re.compile(pattern)
    print(f"Searching for files matching: '{pattern}'...")

    # vol.listdir("/") recursively lists entries
    for entry in output.listdir("/", recursive=True):
        # entry.type 1 is a File, 2 is a Directory
        if entry.type == 1 and regex.search(entry.path):
            
            
            # Define local path (preserving structure if desired)
            local_path = os.path.join(local_dir, os.path.basename(entry.path))
            abs_path_to_file = os.path.abspath(local_path)
            
            # 4. Stream and write the file
            with open(local_path, "wb") as f:
                for chunk in output.read_file(entry.path):
                    f.write(chunk)
                    print(f"Downloaded to: {abs_path_to_file}")

    if os.path.exists(zippath + '.' + zipextension):
        os.remove(zippath + '.' + zipextension)
        print(f"File '{zippath + '.' + zipextension}' has been deleted.")
    else:
        print(f"File '{zippath + '.' + zipextension}' does not exist.")
    num_files = len([entry for entry in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, entry))])
    print(f"Creating '{zippath + '.' + zipextension}' contains '{num_files}' files")
    shutil.make_archive(zippath, zipextension, local_dir)
    print(f"File '{zippath + '.' + zipextension}' created")


@app.local_entrypoint()
def main():
    download_regex_matches.remote(
        volume_name="comfyui-outputs", 
        pattern=r"QWENEditGeneral.*"
    )