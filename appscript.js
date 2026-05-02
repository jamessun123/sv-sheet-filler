const SCRAPER_JSON_FILE_NAME = 'BP16.json'; // Change this to the Drive file name containing the scraper JSON

/**
 * Reads the scraper JSON from a Google Drive file by name.
 * @param {string} fileName
 * @returns {string}
 */
function readJsonFromDriveFile(fileName) {
  const files = DriveApp.getFilesByName(fileName);
  if (!files.hasNext()) {
    throw new Error(`Drive file not found: ${fileName}`);
  }
  const file = files.next();
  return file.getBlob().getDataAsString();
}

function getCraftColor(craft) {
  switch (craft) {
    case 'Forestcraft': return '#6aa84f';
    case 'Runecraft': return '#8e7cc3';
    case 'Dragoncraft': return '#e69138';
    case 'Abysscraft': return '#cc4125';
    case 'Swordcraft': return '#ffd966';
    case 'Neutral': return '#999999';
    default: return '#999999';
  }
}

function getRarityColor(rarity) {
  switch (rarity) {
    case 'Legendary': return '#e06666';
    case 'Gold': return '#ffd966';
    case 'Silver': return '#cccccc';
    case 'Bronze': return '#dd7e6b';
    default: return '#999999';
  }
}

/**
 * Creates a new sheet with card data from the scraper JSON file
 * Format: Normal cards on left, Tokens on right
 */
function createCardSheet() {
  try {
    // Read and parse JSON from Drive file
    const scraperJson = readJsonFromDriveFile(SCRAPER_JSON_FILE_NAME);
    const cards = JSON.parse(scraperJson);
    
    // Separate normal cards from tokens
    const normalCards = [];
    const tokens = [];
    
    for (const card of cards) {
      const cardNo = card.card_no;
      // Extract the second part (after the hyphen and expansion code)
      const parts = cardNo.split('-');
      if (parts.length >= 2) {
        const secondPart = parts[1];
        // Check if it starts with 'T' (token) or digit (normal card)
        if (secondPart[0] === 'T') {
          tokens.push(card);
        } else if (/^\d/.test(secondPart[0])) {
          normalCards.push(card);
        }
      }
    }
    
    // Create a new sheet
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheetName = `Cards_${new Date().getTime()}`;
    const sheet = ss.insertSheet(sheetName);
    
    // Set up headers
    const normalHeaders = ['Name', 'Card Number', 'Craft', 'Rarity', 'Quantity', 'In Decks', 'Available'];
    const tokenHeaders = ['Token Name', 'Card Number', 'Craft', 'Quant', 'In Decks', 'Available'];
    
    // Write normal card headers (columns A-G)
    for (let i = 0; i < normalHeaders.length; i++) {
      sheet.getRange(1, i + 1).setValue(normalHeaders[i]);
    }
    
    // Write token headers (columns I-N, skipping H for spacing)
    for (let i = 0; i < tokenHeaders.length; i++) {
      sheet.getRange(1, i + 9).setValue(tokenHeaders[i]);  // Start at column I (9)
    }
    
    // Write normal card data
    let rowIndex = 2;
    let previousName = null;
    for (const card of normalCards) {
      const cardNumber = card.card_no.replace(/^(.+?-\d+)(?:[A-Z]+)?$/, '$1');
      let displayName = card.name;
      if (previousName === card.name) {
        displayName = `${card.name} (Evolved)`;
      }
      const nameCell = sheet.getRange(rowIndex, 1);
      if (card.link) {
        const richTextValue = SpreadsheetApp.newRichTextValue()
          .setText(displayName)
          .setLinkUrl(card.link)
          .build();
        nameCell.setRichTextValue(richTextValue);
      } else {
        nameCell.setValue(displayName);
      }
      sheet.getRange(rowIndex, 2).setValue(cardNumber);
      sheet.getRange(rowIndex, 3).setValue(card.craft);
      sheet.getRange(rowIndex, 4).setValue(card.rarity);
      sheet.getRange(rowIndex, 5).setValue(0);  // Quantity
      sheet.getRange(rowIndex, 6).setValue(0);  // In Decks
      sheet.getRange(rowIndex, 7).setValue(0);  // Available
      previousName = card.name;
      rowIndex++;
    }
    
    // Write token data
    rowIndex = 2;
    for (const token of tokens) {
      const cardNumber = token.card_no.replace(/^(.+?-\d+)(?:[A-Z]+)?$/, '$1');
      const tokenNameCell = sheet.getRange(rowIndex, 9);
      if (token.link) {
        const richTextValue = SpreadsheetApp.newRichTextValue()
          .setText(token.name)
          .setLinkUrl(token.link)
          .build();
        tokenNameCell.setRichTextValue(richTextValue);
      } else {
        tokenNameCell.setValue(token.name);
      }
      sheet.getRange(rowIndex, 10).setValue(cardNumber);  // Column J
      sheet.getRange(rowIndex, 11).setValue(token.craft); // Column K
      sheet.getRange(rowIndex, 12).setValue(0);           // Column L - Quant
      sheet.getRange(rowIndex, 13).setValue(0);           // Column M - In Decks
      sheet.getRange(rowIndex, 14).setValue(0);           // Column N - Available
      rowIndex++;
    }
    
    // Determine the number of rows used by either section
    const maxRows = Math.max(normalCards.length, tokens.length) + 1;
    const sheetRange = sheet.getRange(1, 1, maxRows, 14);
    sheetRange
      .setBackground('#999999')
      .setFontColor('#ffffff')
      .setFontWeight('normal')
      .setHorizontalAlignment('left')
      .setVerticalAlignment('bottom');
    
    // Format header row
    const headerRange = sheet.getRange(1, 1, 1, 14);
    headerRange.setFontWeight('bold');

    // Apply craft and rarity cell colors
    for (let i = 0; i < normalCards.length; i++) {
      const row = 2 + i;
      sheet.getRange(row, 3).setBackground(getCraftColor(normalCards[i].craft));
      sheet.getRange(row, 4).setBackground(getRarityColor(normalCards[i].rarity));
    }

    for (let i = 0; i < tokens.length; i++) {
      const row = 2 + i;
      sheet.getRange(row, 11).setBackground(getCraftColor(tokens[i].craft));
    }
    
    // Auto-resize columns for better visibility
    for (let i = 1; i <= 14; i++) {
      sheet.autoResizeColumn(i);
    }
    
  } catch (error) {
    SpreadsheetApp.getUi().alert(`Error: ${error.message}`);
  }
}

/**
 * Create a menu item in Google Sheets for easier access
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Card Tools')
    .addItem('Create Card Sheet', 'createCardSheet')
    .addToUi();
}
