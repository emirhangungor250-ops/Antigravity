require('dotenv').config();

const BASE_URL = 'http://localhost:3001'; // Lokal sunucuda test edeceğiz

const testCases = [
  {
    name: "1. Eksik Veri (answer_1 yok)",
    payload: {
      transaction_id: "test_tx_001",
      first_name: "Doomsday",
      last_name: "Test"
      // answer_1 bilerek yok
    },
    expectedStatus: 400
  },
  {
    name: "2. Tamamen Alakasız Metin (Telefon Yok)",
    payload: {
      transaction_id: "test_tx_002",
      first_name: "NoPhone",
      last_name: "Test",
      answer_1: "Ben telefon kullanmıyorum, güvercinle haberleşiyorum."
    },
    expectedStatus: 200 // Email fallback'e düşmeli, request başarılı sayılır
  },
  {
    name: "3. Çok Uzun ve Karmaşık Cevap İçinden Telefon Çıkarma",
    payload: {
      transaction_id: "test_tx_003",
      first_name: "ComplexText",
      last_name: "Test",
      answer_1: "Merhaba, bana şu numaradan ulaşabilirsiniz: sıfır beş yüz otuz üç altı yüz altmış altı yirmi bir on üç, eğer açmazsam ablamın numarası 532 111 22 33."
    },
    expectedStatus: 200 // Groq LLM bunu yakalayıp ilk numarayı alabilmeli
  },
  {
    name: "4. New Paid Member Gelmeden Direkt Questions Gelmesi (Race Condition)",
    payload: {
      transaction_id: "test_tx_004_race",
      first_name: "Race",
      last_name: "Condition",
      answer_1: "0533 123 45 67"
    },
    expectedStatus: 200 // Notion createMember yapmalı
  },
  {
    name: "5. Duplicate Kayıt (Aynı numara başka hesapta)",
    payload: {
      transaction_id: "test_tx_005_dup",
      first_name: "Duplicate",
      last_name: "Test",
      answer_1: "0533 123 45 67" // Bir önceki testte eklendi
    },
    expectedStatus: 200 // skipped: true dönmeli
  }
];

async function runDoomsdayTest() {
  console.log("🔥 WHATSAPP ONBOARDING KIYAMET TESTİ BAŞLIYOR 🔥\n");
  
  let successCount = 0;
  
  for (const test of testCases) {
    console.log(`\n⏳ TEST: ${test.name}`);
    try {
      const response = await fetch(`${BASE_URL}/webhook/membership-questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(test.payload)
      });
      
      const responseData = await response.json().catch(() => ({}));

      if (response.status === test.expectedStatus) {
        console.log(`✅ BAŞARILI (Status: ${response.status}) -> Sonuç:`, responseData);
        successCount++;
      } else {
        console.log(`❌ BEKLENMEYEN STATUS (Beklenen: ${test.expectedStatus}, Gelen: ${response.status})`);
        console.log(`Data:`, responseData);
      }
    } catch (error) {
       console.error(`❌ BEKLENMEYEN HATA:`, error.message);
    }
  }
  
  console.log(`\n======================================================`);
  console.log(`🏁 TEST SONUCU: ${testCases.length} testin ${successCount} tanesi başarıyla beklendiği gibi davrandı.`);
  console.log(`======================================================`);
}

runDoomsdayTest();
