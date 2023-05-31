"""
This python file was written to quickly update the ASTR3010 MESA models with new parameters, rather than
manually going through and updating all the files.

To run it from the terminal, use the following command:

python update_model.py

"""
# All packages are built-in so don't require a virtual environment
from pathlib import Path
import re
import subprocess


""" Initial Parameters - Edit these """
model_path = '../data/mesa_model'   # Path to the model directory. Defaults to a model called 'mesa_model', saved in the data folder
mesa_dir = '/opt/mesa'  # Path to the MESA directory. On MQ VMs, this is at /opt/mesa

initial_mass = 1.0  # Initial mass of the star in solar masses. Default = 1.0
initial_z = 0.02  # Initial metallicity of the star. Default = 0.02

rebuild = True  # If True, will rebuild the model by clearing LOG, cache, nohup, and mod files. 
                # Leave false to just run the existing model.
run_after = True  # If True, will run the model after updating the files


""" Variable Checks - Don't edit below this line """
# Check directories exist
mesa_dir = Path(mesa_dir)
if not mesa_dir.exists():
    raise FileNotFoundError(f'Could not find MESA directory: {mesa_dir}')

model_path = Path(model_path)
if not model_path.exists():
    raise FileNotFoundError(f'Could not find model path: {model_path}')

# Check the version of MESA is correct. ASTR3010 code only works with version 15140.
with open(mesa_dir / 'data' / 'version_number', 'r') as f:
    version = f.read().strip()

if version != '15140':
    raise ValueError(f'MESA version {version} is not supported. Must be 15140')

# Check variable bounds
if initial_mass <= 0:
    raise ValueError(f'Initial mass {initial_mass} is not valid. Must be positive!')

if not (0 <= initial_z <= 0.04):
    raise ValueError(f'Initial Z {initial_z} is not valid. Must be between 0 and 0.04')

# Convert variables to string format
initial_mass = f'{initial_mass:.2f}d0'
initial_z = f'{initial_z:.2f}d0'


""" File Adjustments and Rebuild """
def replace_values(lines: list[str]) -> list[str]:
    """
    Replace the matched values from 'regex_vals' from a file.

    :param lines: All lines read in from a file
    :return: The new lines with replaced variables
    """
    for i, l in enumerate(lines):
        for pattern, replace in regex_vals:
            if len(re.findall(pattern, l)) > 0:
                lines[i] = re.sub(pattern, replace, l)
                break
    
    return lines

if rebuild:
    files = list(model_path.glob('inlist*'))
    files.append(model_path / 'rn')
    files.append(model_path / 'make' / 'makefile')

    # List of regex patterns to match and replace
    regex_vals = [
        ('MESA_DIR = .*', f'MESA_DIR = {mesa_dir}'),  # Matches only makefile which doesn't use quotes
        ('mesa_dir = .*', f"mesa_dir = '{mesa_dir}'"),  # Matches inlist headers which require quotes
        ('initial_mass = .*', f'initial_mass = {initial_mass}'),
        ('initial_z = .*', f'initial_z = {initial_z}'),
        ('!pgstar_flag', 'pgstar_flag'),
        ('#do_one inlist_', 'do_one inlist_')  # .rn file has most stages commented out
    ]

    # Replace all the regex values in all files
    print(f'Updating {len(files)} files...')

    for f_path in files:
        with open(f_path, 'r') as f:
            in_lines = f.readlines()

        out_lines = replace_values(in_lines)

        with open(f_path, 'w') as f:
            f.writelines(out_lines)

    """ Clearing Old Files """
    # Remove nohup.out file
    (model_path / 'nohup.out').unlink(missing_ok = True)

    # Clear old log files
    files = model_path.glob('LOGS*/*')
    for f in files:
        f.unlink()
    
    print(f'Cleared {len(list(files))} old LOG files.')
    
    # Clear the cache
    files = list(mesa_dir.glob('**/cache/*')) + list(model_path.glob('.mesa_temp_cache/*'))
    for f in mesa_dir.glob('**/cache/*'):
        f.unlink()
    
    print(f'Cleared {len(list(files))} cached files.')

    # Remove star
    (model_path / 'star').unlink(missing_ok = True)

    # Clear old .mod files
    files = model_path.glob('*.mod')
    for f in files:
        f.unlink()
    
    print(f'Cleared {len(list(files))} old .mod files.')


""" Running the Model """""
if run_after:
    print(f'Running model {model_path.name}')
    print(f'Initial M: {initial_mass}')
    print(f'Initial Z: {initial_z}')
    
    subprocess.call('./clean', cwd=str(model_path), shell=True)  # Remove old files and clean
    subprocess.call('./mk', cwd=str(model_path), shell=True)  # Run the makefile code
    subprocess.call('nohup ./rn &', cwd=str(model_path), shell=True)  # Run the model in the background
