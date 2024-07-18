import os
import subprocess
#only doing first 8 1 -8 
#TODO
#DO 1-8   9-16,  17-24, 25-32
#range 1-7 9-15, 17-23, 25-31

#missing 8,16,24,32 --> for the last run do 24-33  
# List of XML directory paths
xml_folders = [f"/mnt/data1/kjsidhu/filtered_results/split_{i}" for i in range(24, 33)]
xml_folders.append("/mnt/data1/kjsidhu/filtered_results/split_8")
xml_folders.append("/mnt/data1/kjsidhu/filtered_results/split_16")
# Define the shared output and stderr folders
output_folder = "/mnt/data1/kjsidhu/Chemical_filtered_jsons"
stderr_folder = "/mnt/data1/kjsidhu/memoSTDERR"

def run_script(xml_folder, output_folder, stderr_folder):
    # Command to run your initial script
    command = f"python3 memo.py {xml_folder} {output_folder} {stderr_folder}"
    # Start the subprocess and return the process handle
    return subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if __name__ == "__main__":
    processes = []

    # Start all processes
    for xml_folder in xml_folders:
        processes.append(run_script(xml_folder, output_folder, stderr_folder))

    # Wait for all processes to complete and capture outputs
    for process in processes:
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            print(f"Error in process: {process.args}\n{stderr.decode('utf-8')}")
        else:
            print(f"Process completed successfully: {process.args}\n{stdout.decode('utf-8')}")
