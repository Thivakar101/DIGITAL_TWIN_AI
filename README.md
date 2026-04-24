# Digital Twin AI

## Overview
Digital Twin AI is a localized, intelligent assistant designed around a customizable persona framework. It provides a multi-faceted interface, including a web-based application, a PyQt desktop client, and a lightweight HTTP API. The system utilizes an in-process memory layer to retain conversational context and user preferences, enabling the assistant to simulate decisions and interact consistently according to an established personality profile.

## System Architecture

The project is structured into several core components that work in tandem to provide the digital twin experience:

- **Core Logic (`twin_core.py`)**: This module contains the foundational mechanisms for defining the persona, processing chat interactions, and simulating decisions. It interprets survey data to derive personality traits, tone, and decision-making styles.
- **Memory Management (`memory_bank.py`)**: An in-memory storage system that utilizes similarity search. It archives survey responses, past conversations, and previous decisions, allowing the core logic to retrieve relevant context for grounded interactions.
- **Model Integration (`local_model_client.py` and `gemini_client.py`)**: The application interfaces primarily with local Ollama models for chat and embeddings. It also includes provisions for Gemini API integration.
- **Interfaces**:
  - **HTTP Server (`server.py`)**: Serves the static web assets located in the `web/` directory and exposes a RESTful JSON API.
  - **Desktop Application (`ui.py`)**: A PyQt5-based graphical user interface for direct interaction.
- **Configuration (`app_config.py`)**: Manages environment variables and configuration settings, persisting them to a local `.env` file.

## Prerequisites

To operate Digital Twin AI, the following prerequisites must be met:
- Python 3.10 or higher.
- A local installation of Ollama, accessible at `http://127.0.0.1:11434`.
- A compatible language model pulled via Ollama (e.g., `llama3`).

## Installation and Setup

1. Create and activate a Python virtual environment to isolate project dependencies:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install the required dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Ensure that the Ollama service is running in the background to provide live model responses.

## Usage

### Running the Web Application
To initialize the HTTP server and access the web interface, execute:
```powershell
python server.py
```
The server will typically listen on `http://127.0.0.1:8000`. Navigate to this address in a web browser.

### Running the Desktop Application
To launch the standalone PyQt interface, execute:
```powershell
python ui.py
```

## Configuration

The application maintains its configuration within a `.env` file located in the project root directory. The following parameters are supported:

- `USER_NAME`: The default display name of the user.
- `OLLAMA_MODEL`: The designated Ollama model (defaults to `llama3`).
- `OLLAMA_BASE_URL`: The URL for the Ollama server (defaults to `http://127.0.0.1:11434`).
- `GEMINI_API_KEY`: The API key required for Gemini integration, if applicable.

Configuration settings can be modified directly through the web interface or the desktop application's settings menu. Changes are automatically persisted to the `.env` file.

## API Endpoints

The HTTP server provides the following endpoints for programmatic interaction:

- `GET /api/status`: Retrieves the current persona and model operational status.
- `GET /api/memories`: Returns serialized memory entries.
- `POST /api/settings`: Updates the user name or model configurations.
- `POST /api/survey`: Submits responses for the persona survey.
- `POST /api/chat`: Processes an incoming chat message and returns a response.
- `POST /api/simulate`: Executes a decision simulation based on provided context.