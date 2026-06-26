const input = "Telefon: 0 (532) 123 45 67";
const cleaned = input.replace(/^(telefon|tel|cep|numara|no|whatsapp|wa)[:\-\s]*/i, '').trim();
console.log("Cleaned:", cleaned);
const isValid = /^[\d\s\-\(\)\.\+\/]+$/.test(cleaned);
console.log("isValid:", isValid);
