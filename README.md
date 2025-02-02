# CS:GO Medal Parser

A Python script to parse medals, coins, and pins from the CS:GO API.  
This project is specifically designed to work with the [ByMykel API](https://github.com/ByMykel/CSGO-API).

## Features

- **Image Cropping**: Automatically crops downloaded images.
- **Efficient Caching**: Avoids redundant downloads by caching already retrieved images.

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/tom-jm69/cs-medal-parser.git
   cd cs-medal-parser
   ```

2. **Create and activate a virtual environment** (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run `main.py` to parse medals, coins, and pins from the CS:GO API (ByMykel):

```bash
python main.py
```

Parsed data and images will be saved in the appropriate directory.

## Configuration

Modify `config.py` to customize settings like API keys or image storage locations.

## Docker

You can also run the project using Docker:

1. **Build the Docker image**:

   ```bash
   docker build -t cs-medal-parser .
   ```

2. **Run the container**:

   ```bash
   docker run --rm -v $(pwd)/output:/app/output cs-medal-parser
   ```

This ensures that the output data is saved in the `output` directory of your current working directory.

## Cronjob

Update the images every 15 minutes:

```bash
*/15 * * * * docker compose -f /home/ubuntu/python/bots/cs-medal-parser/docker-compose.yml run --rm cs2medalparser >> /home/ubuntu/python/bots/cs-medal-parser/logs/medalparser.log 2>&1
```

## API

This script retrieves medal, coin, and pin data using the **ByMykel API**.  
For more details, visit: [ByMykel API Documentation](https://bymykel.github.io/CSGO-API/)

## License

This project is licensed under the GPL-3.0 License. See the [LICENSE](LICENSE) file for details.
