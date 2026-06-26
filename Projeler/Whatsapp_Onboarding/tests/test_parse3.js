const { parsePhoneNumberFromString } = require('libphonenumber-js');
console.log("905321234567: ", parsePhoneNumberFromString('905321234567', 'TR')?.number || 'failed');
console.log("05321234567: ", parsePhoneNumberFromString('05321234567', 'TR')?.number || 'failed');
console.log("5321234567: ", parsePhoneNumberFromString('5321234567', 'TR')?.number || 'failed');
