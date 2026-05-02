/**
 * Inspect formatting for a given sheet and output cell style details to a new sheet.
 *
 * Usage:
 * 1. Open your Google Sheets Apps Script editor.
 * 2. Add this script file to the project.
 * 3. Run inspectSheetFormatting('SheetName') or inspectSheetFormatting() for active sheet.
 *
 * The script will create a new sheet named StyleInspect_<SheetName>_<timestamp>.
 */
function inspectSheetFormatting(sheetName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = sheetName ? ss.getSheetByName(sheetName) : ss.getActiveSheet();
  if (!sheet) {
    throw new Error(`Sheet not found: ${sheetName}`);
  }

  const dataRange = sheet.getDataRange();
  const values = dataRange.getValues();
  const backgrounds = dataRange.getBackgrounds();
  const fontColors = dataRange.getFontColors();
  const fontWeights = dataRange.getFontWeights();
  const fontStyles = dataRange.getFontStyles();
  const horizontalAlignments = dataRange.getHorizontalAlignments();
  const verticalAlignments = dataRange.getVerticalAlignments();
  const numberFormats = dataRange.getNumberFormats();
  const wrapStrategies = dataRange.getWrapStrategies();
  const notes = dataRange.getNotes();
  const formulas = dataRange.getFormulas();
  const textStyles = dataRange.getTextStyles();

  const outputSheetName = `StyleInspect_${sheet.getName()}_${new Date().getTime()}`;
  const outputSheet = ss.insertSheet(outputSheetName);

  const headers = [
    'Row',
    'Column',
    'Address',
    'Value',
    'Formula',
    'Background',
    'Font Color',
    'Font Weight',
    'Font Style',
    'Underline',
    'Strikethrough',
    'Font Family',
    'Font Size',
    'Horizontal Align',
    'Vertical Align',
    'Number Format',
    'Wrap Strategy',
    'Note'
  ];

  outputSheet.getRange(1, 1, 1, headers.length).setValues([headers]);

  const rows = [];
  for (let r = 0; r < values.length; r++) {
    for (let c = 0; c < values[r].length; c++) {
      const textStyle = textStyles[r][c];
      rows.push([
        r + 1,
        c + 1,
        sheet.getRange(r + 1, c + 1).getA1Notation(),
        values[r][c],
        formulas[r][c],
        backgrounds[r][c],
        fontColors[r][c],
        fontWeights[r][c],
        fontStyles[r][c],
        textStyle.isUnderline(),
        textStyle.isStrikethrough(),
        textStyle.getFontFamily(),
        textStyle.getFontSize(),
        horizontalAlignments[r][c],
        verticalAlignments[r][c],
        numberFormats[r][c],
        wrapStrategies[r][c],
        notes[r][c]
      ]);
    }
  }

  if (rows.length > 0) {
    outputSheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
  }

  outputSheet.autoResizeColumns(1, headers.length);
  SpreadsheetApp.getUi().alert(`Style inspector sheet created: ${outputSheetName}`);
}

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Style Inspector')
    .addItem('Inspect Active Sheet', 'inspectSheetFormatting')
    .addToUi();
}
