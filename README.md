# My Python Project

This project is designed to read Plenarprotokolle from the bundesAPI. It provides functionality to make API requests and process the responses effectively.

## Project Structure

```
the-project
├── src
│   ├── main.py          # Entry point of the application
│   └── utils
│       └── __init__.py  # Utility functions for API interactions
├── requirements.txt     # Project dependencies
├── .gitignore           # Files and directories to ignore in Git
└── README.md            # Project documentation
```

## Setup Instructions

1. Clone the repository:

   ```
   git clone <repository-url>
   cd the_project
   ```

2. Install the required dependencies:

### **`macOS`** type the following commands :

- Install the virtual environment and the required packages by following commands:

  ```BASH
  pyenv local 3.11.3
  python -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  ```

### **`WindowsOS`** type the following commands :

- Install the virtual environment and the required packages by following commands.

  For `PowerShell` CLI :

  ```PowerShell
  pyenv local 3.11.3
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  ```

  For `Git-Bash` CLI :

  ```BASH
    pyenv local 3.11.3
    python -m venv .venv
    source .venv/Scripts/activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
  ```

## Usage

To run the application, execute the following command:

```
python src/main.py
```

## About bundesAPI

The bundesAPI provides access to various governmental data, including Plenarprotokolle. This project utilizes the API to fetch and display relevant information.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.
