# Mesa Runner
This is a basic project template put together for the ASTR3010 unit at Macquarie University, with the goal of simplifying the setup process of running MESA models.

Included in this project are:
- A brief script to update the MESA model template with user-defined masses and metallicities.
- A pre-defined list of python packages used in the project, including the 'mesa-reader' package only available through [GitHub](https://github.com/wmwolf/py_mesa_reader.git). These packages are used in the ipynb file provided.
- A basic project structure for managing code, data, and code outputs.

## Setup
Note that the provided script relies solely on built-in packages, and so doesn't require the full project setup. Skip to the `Usage` section if that's all you plan on using in this project.

This project uses poetry to manage python packages in a virtual environment. To set up poetry, follow their [Installation Guide](https://python-poetry.org/docs/#installation).
Then, setup and install the project by typing the following into the terminal:
```bash
poetry install
poetry shell
```

## Usage
To use the 'update_model' script,
1. Update the initial parameters of the script. Their usage is commented in the code.
2. Run the script using `python ./src/update_model.py`

The Jupyter notebook provided for the unit is used for the analysis of all MESA outputs.