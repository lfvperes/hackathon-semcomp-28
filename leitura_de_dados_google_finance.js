// Instalar a biblioteca
// npm install googleapis

const { google } = require('googleapis');

// Configurar autenticação
const auth = new google.auth.GoogleAuth({
  keyFile: 'credentials.json',
  scopes: ['https://www.googleapis.com/auth/spreadsheets'],
});

const sheets = google.sheets({ version: 'v4', auth });

async function readSheet() {
  try {
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: 'https://docs.google.com/spreadsheets/d/1HO-EfxLBAFfrCPgLkzI0BI3g5YhPMycIAOVEA-7Jy68/edit?gid=0#gid=0',
      range: 'Página1!A1:B5', // Intervalo que deseja ler
    });

    console.log(response.data.values);
    return response.data.values;
  } catch (error) {
    console.error('Erro:', error);
  }
}