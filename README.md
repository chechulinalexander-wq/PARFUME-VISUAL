# Perfume Visual - Background Removal

This project uses Google's Gemini 2.5 Flash Image API to separate perfume bottles from their backgrounds.

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Get your Gemini API key:**
   - Go to: https://aistudio.google.com/app/apikey
   - Create a new API key
   - Copy the key

3. **Configure API key:**
   - Open `.env` file
   - Replace `your_api_key_here` with your actual API key

## Usage

Run the script:
```bash
python process_perfume.py
```

The script will:
1. Download the perfume bottle image from the source URL
2. Send it to Gemini API with a prompt to remove the background
3. Save both the original and processed images to the `img/` folder

## Output

- `img/original_perfume.jpg` - Original downloaded image
- `img/perfume_no_background.png` - Processed image with background removed

## API Documentation

- [Gemini API Image Generation](https://ai.google.dev/gemini-api/docs/image-generation?hl=ru)
- [Get Started with Gemini API](https://ai.google.dev/gemini-api/docs/get-started/tutorial?hl=ru)


