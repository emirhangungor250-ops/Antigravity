const input = "Telefon: 0 (532) 123 45 67";
const cleaned = input.replace(/^(tel|telefon|cep|no|numara)[:\-\s]*/i, '').trim();
console.log("Cleaned:", cleaned);
const isValid = /^[\d\s\-\(\)\.\+\/]+$/.test(cleaned);
console.log("isValid:", isValid);
