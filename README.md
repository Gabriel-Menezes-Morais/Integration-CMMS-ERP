# CMMS-ERP Integration System

## Description

This system is a web application developed in Python using Streamlit for integration between CMMS (Computerized Maintenance Management System) and ERP (Enterprise Resource Planning) systems. The main objective is to automate maintenance product management, item demand generation, and synchronization with the ERP after allocation, reducing rework and improving MTTR (Mean Time To Repair) metrics.

## Main Features

- **User Authentication**: Secure login system with user management via API
- **Stock Monitoring**: Automatic verification of minimum vs. current stock levels
- **Demand Generation**: Automatic creation of purchase needs based on low stock
- **Shopping Cart**: Interface to manage items needed for maintenance
- **Material Registration (PDM)**: Guided creation of standardized material descriptions with dynamic taxonomy
- **API Integration**: Connection with external APIs for parts and user data
- **Data ETL**: Extraction, transformation, and loading processes
- **Interactive Dashboard**: Intuitive web interface for visualization and management

## System Architecture

### Directory Structure

```
sistema_AutNec/
├── config/                 # Configuration files
│   ├── config.yaml        # User and authentication settings
│   └── log_config.json    # Logging configuration
├── custom/                # Custom files
│   └── style.css         # CSS styles for the interface
├── database/              # Database functions
│   └── funcoesBD.py      # SQL Server connections and operations
├── ETL/                   # ETL processes
│   ├── listas.py         # Generation of needs lists
│   ├── monitor.py        # Stock monitoring
│   ├── transformacao_usuarios.py  # User data transformation
│   └── Transformacao.py  # General data transformation
├── images/                # Application images
├── pages/                 # Streamlit pages
│   └── Cadastrar_Item.py  # Material registration (PDM)
├── services/              # External API integrations
│   ├── integra_API_Cadastro.py  # API for item registration
│   ├── integra_API_ListarPecas.py  # API for parts listing
│   └── integra_API_Usuarios.py     # API for users
├── custom_log.py          # Custom logging configuration
├── streamlit_app.py       # Main Streamlit application
├── streamlit_app_TESTE.py # Test version of the application
├── requirements.txt       # Python dependencies
├── LICENSE                # Project license
└── README.md             # This file
```

### Technologies Used

- **Python 3.x**: Main language
- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **SQLAlchemy**: Database ORM
- **Requests**: HTTP client for APIs
- **PyYAML**: YAML file manipulation
- **Streamlit-Authenticator**: User authentication
- **SQL Server**: Main database
- **ODBC Driver**: SQL Server connection

## Prerequisites

- Python 3.8 or higher
- SQL Server with ODBC Driver 18
- Access to external APIs (CMMS and authentication)
- Environment variables configured (.env)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd sistema_AutNec
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file in the project root with the following variables:
   ```
   DB_SERVER=your_sql_server
   DB_NAME=database_name
   DB_UID=db_user
   DB_PWD=db_password
   ENDPOINT=parts_api_url
   TOKEN=parts_api_token
   ENDPOINT_AUTENTICACAO=users_api_url
   TOKEN_AUTENTICACAO=users_api_token
   ```

5. **Configure the database**:
   - Ensure the necessary tables exist in SQL Server
   - Main table: `CadNecComCOPY`

## Configuration

### config.yaml File
Contains user credentials for authentication. Structure:
```yaml
credentials:
  usernames:
    user:
      id: 'ID'
      email: email@domain.com
      name: Full Name
      password: password
      ativo: true
      executante: Yes
```

### log_config.json File
Structured logging configuration for different alert levels.

## Usage

### Running the Application

1. **Activate the virtual environment**:
   ```bash
   .venv\Scripts\activate
   ```

2. **Run the application**:
   ```bash
   streamlit run streamlit_app.py
   ```

3. **Access in browser**:
   Open `http://localhost:8501`

### Interface Features

- **Login**: User authentication
- **Dashboard**: Visualization of maintenance needs
- **Cart**: Management of items for purchase
- **Monitoring**: Automatic stock verification
- **PDM Registration**: Structured item creation with auto-generated codes and description preview

### Material Registration (Cadastrar_Item.py)

Steps to register a new item via the PDM page:
1. Choose a base family or create a new one ("Base Name"), then create a new family if needed.
2. Pick a type or add a new one with allowed variations and required technical specs.
3. Optionally add new variations (finishes) for an existing type.
4. Fill in the technical specifications requested for the selected family/type and choose the unit of measure.
5. Review the auto-generated description preview and the next sequential code (mntXXXX).
6. Submit to register the item: it calls the external registration API, persists in the ERP via `CadastrarBD`, and stores a local JSON history in `itens_cadastrados.json`. Existing taxonomy lives in `taxonomia_materiais.json` and is extended on the fly by the page.

## ETL Processes

### Stock Monitoring
- Automatically performs stock level checks
- Compares current vs. minimum stock
- Generates alerts for items below minimum

### Data Transformation
- Cleaning and standardization of numeric data
- Conversion of financial formats
- Handling of boolean values

### API Integration
- Extraction of parts data from CMMS
- User synchronization
- Automatic retry in case of failures

## Database

### Main Tables
- `CadNecComCOPY`: Stores purchase needs

### Operations
- Query items in cart
- Insert new needs
- Update order status

## Logs and Monitoring

The system uses structured logging with two levels:
- `app.lowlevel`: Informational and debug logs
- `app`: Alert and error logs

## Contributing

1. Fork the project
2. Create a branch for your feature (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

This project is licensed under the [MIT License](LICENSE).

## Support

For technical support or questions:
- Email: gabriel.menezes.mata@gmail.com
- Internal company documentation

## Implemented Improvements

- Automation in item demand generation
- Automatic synchronization with ERP
- Reduction of manual rework
- Improvement in MTTR metrics
- Intuitive interface for maintenance users
