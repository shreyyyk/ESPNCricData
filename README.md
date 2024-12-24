# Scraper for Match Scorecards

This repository contains a scraper for extracting data from match scorecards. While the scraper is functional, it is currently producing inconsistent data due to variations in the HTML structure across different scorecards. This issue will require further debugging and updates to the parsing logic to ensure consistent data extraction.

## Current Status
- **Working**: The scraper can successfully fetch and process data from scorecards.
- **Issues**: Inconsistent data due to differences in HTML structure between scorecards.

## Next Steps
1. Analyze the variations in the HTML structure across different scorecards.
2. Update the scraper logic to handle these variations.
3. Implement tests to validate the consistency and accuracy of the extracted data.

## Usage
1. Clone the repository:
   ```bash
   git clone https://github.com/Shreyyyk/ESPNCricData.git
   ```
2. Navigate to the project directory:
   ```bash
   cd Data
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the scraper:
   ```bash
   python scraper.py
   ```

## Contribution
Contributions are welcome! If you have suggestions or can help address the HTML structure variations, please create a pull request or open an issue.


