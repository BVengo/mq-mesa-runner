"""
This python file was written to quickly update the ASTR3010 MESA models with
new parameters, rather than manually going through and updating all the files.

To run it from the terminal, use the following command:

python update_model.py
"""

# All packages are built-in so don't require a virtual environment
from pathlib import Path
import re
import subprocess


#############################################
# Initial Paramters - Edit these.
#############################################
# Path to the model directory
model_path = '../data/mesa_model'

# Path to the MESA directory. On MQ VMs, this is at /opt/mesa
mesa_dir = '/opt/mesa'

# Initial mass of the star in solar masses. Default = 1.0
initial_mass = 1.0

# Initial metallicity of the star. Default = 0.02
initial_z = 0.02

# Rebuilding will clear LOG, cache, nohup, and mode files. Leave false if you
# just want to re-run the existing model. Note that any changes to inlist files
# will require an entire rebuild. However, adjusting the .rn file will not, so
# you can still start models halfway through.
rebuild = True

# Do you want to run the model immediately after?
run_after = True


#############################################
# Model Update Code - Do not modify.
#############################################
# Check directories exist
mesa_dir = Path(mesa_dir)
if not mesa_dir.exists():
    raise FileNotFoundError(f'Could not find MESA directory: {mesa_dir}')

model_path = Path(model_path)
if not model_path.exists():
    raise FileNotFoundError(f'Could not find model path: {model_path}')

# Check the version of MESA is correct. ASTR3010 code only works
# with version 15140.
with open(mesa_dir / 'data' / 'version_number', 'r') as f:
    version = f.read().strip()

if version != '15140':
    err = f'MESA version {version} is not supported. Must be 15140'
    raise ValueError(err)

# Check variable bounds
if initial_mass <= 0:
    err = f'Initial mass {initial_mass} is not valid. Must be positive!'
    raise ValueError(err)

if not (0 <= initial_z <= 0.04):
    err = f'Initial Z {initial_z} is not valid. Must be between 0 and 0.04'
    raise ValueError(err)

# Convert variables to string format
initial_mass = f'{initial_mass:.2f}'
initial_z = f'{initial_z:.2f}d0'


def replace_values(lines: list[str], regex_vals) -> list[str]:
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
        # Set MESA_DIR in makefile (no quotes required)
        ('MESA_DIR = .*', f'MESA_DIR = {mesa_dir}'),
        # Set mesa_dir in inlist headers (requires quotes)
        ('mesa_dir = .*', f"mesa_dir = '{mesa_dir}'"),
        # Setting initial mass in inlist files
        ('initial_mass = .*', f'initial_mass = {initial_mass}'),
        # Setting initial metallicity in inlist files
        ('initial_z = .*', f'initial_z = {initial_z}'),
        # Show the plotting window for all stages
        ('!pgstar_flag', 'pgstar_flag'),
        # Enable all stages in the .rn file
        ('#do_one inlist_', 'do_one inlist_'),
        ('#cp start_he_core_flash_mode', 'cp start_he_core_flash_mode'),
        # Remove the maximum model limit - it stops MESA runs from completing
        ('max_model_number', '! max_model_number')
    ]

    # Replace all the regex values in all files
    print(f'Updating {len(files)} files...')

    for f_path in files:
        with open(f_path, 'r') as f:
            in_lines = f.readlines()

        out_lines = replace_values(in_lines, regex_vals)

        with open(f_path, 'w') as f:
            f.writelines(out_lines)

    # Adjust star birth limit to be based on hydrogen burning
    # rather than luminosity
    termination_line = 'required_termination_code_string'
    luminosity_limit = 'log_L_lower_limit'
    hydrogen_limit = 'power_h_burn_upper_limit'

    regex_vals = [
        (
            f'{termination_line} = \'{luminosity_limit}\'',
            f'{termination_line} = \'{hydrogen_limit}\''
        ),
        (
            f'{luminosity_limit} .*',
            f'{hydrogen_limit} = 0.001'
        )
    ]

    with open(model_path / 'inlist_start', 'r') as f:
        in_lines = f.readlines()

    out_lines = replace_values(in_lines, regex_vals)

    with open(model_path / 'inlist_start', 'w') as f:
        f.writelines(out_lines)

    """ Clearing Old Files """
    # Remove nohup.out file
    (model_path / 'nohup.out').unlink(missing_ok=True)

    # Clear old log files
    files = model_path.glob('LOGS*/*')
    for f in files:
        f.unlink()

    print(f'Cleared {len(list(files))} old LOG files.')

    # Clear the cache
    files = list(mesa_dir.glob('**/cache/*')) + \
        list(model_path.glob('.mesa_temp_cache/*'))
    for f in mesa_dir.glob('**/cache/*'):
        f.unlink()

    print(f'Cleared {len(list(files))} cached files.')

    # Remove star
    (model_path / 'star').unlink(missing_ok=True)

    # Clear old .mod files
    files = model_path.glob('*.mod')
    for f in files:
        f.unlink()

    print(f'Cleared {len(list(files))} old .mod files.')


""" Running the Model """
if run_after:
    print(f'Running model {model_path.name}')
    print(f'Initial M: {initial_mass}')
    print(f'Initial Z: {initial_z}')

    # Remove old files and clean
    subprocess.call('./clean', cwd=str(model_path), shell=True)

    # Run the makefile code
    subprocess.call('./mk', cwd=str(model_path), shell=True)

    # Run the model in the background. Outputs to nohup.out
    subprocess.call('nohup ./rn &', cwd=str(model_path), shell=True)
