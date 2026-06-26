const { parsePhoneNumberFromString } = require('libphonenumber-js');
const phone = parsePhoneNumberFromString('0 (532) 123 45 67', 'TR');
console.log(phone ? phone.isValid() : 'failed');
