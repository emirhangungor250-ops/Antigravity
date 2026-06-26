// scripts/simulation_scenarios.js
//
// SABLON: Bu dosya, asistanin bilgi tabani + prompt + RAG zincirini test eden
// senaryo listesidir. Asagidakiler ORNEK/PLACEHOLDER senaryolardir — kendi
// bilgi tabaniniza ve is akisiniza gore doldurun/cogaltin.
//
// Her senaryo: { id, name, category, turns: [{ user, expect }] }
// expect:
//   mustContain:    (string | RegExp)[]  — cevapta hepsi gecmeli
//   mustNotContain: (string | RegExp)[]  — cevapta hicbiri gecmemeli
//   toolExpected:   boolean              — eskalasyon tool'u cagirilmali mi
//
// Cok-turn senaryolar icin turns dizisine birden fazla { user, expect } koyun;
// boylece hafiza / profil tutarliligi / tekrar bug'lari da test edilir.

// Ortak yasakli pattern ornekleri — kendi kurallariniza gore guncelleyin
const NO_EM_DASH = [/ — /, /:\s*—/, /\n—\s/];

module.exports = [
  {
    id: 1,
    category: 'discovery',
    name: 'Ornek — yalin selamlama, kesif sorusu beklenir',
    turns: [
      {
        user: 'Merhaba',
        expect: {
          mustContain: [/[?]/],          // bir kesif sorusu sormali
          mustNotContain: NO_EM_DASH,
        },
      },
    ],
  },
  {
    id: 2,
    category: 'info',
    name: 'Ornek — bilgi tabaninda olan soru, dogru bilgi donmeli',
    turns: [
      {
        user: '[KULLANICI SORUSU]',
        expect: {
          mustContain: ['[CEVAPTA GECMESI GEREKEN IFADE]'],
          mustNotContain: NO_EM_DASH,
          toolExpected: false,
        },
      },
    ],
  },
  {
    id: 3,
    category: 'escalation',
    name: 'Ornek — bilgi tabani disi / hassas soru, eskalasyon beklenir',
    turns: [
      {
        user: '[KAPSAM DISI VEYA HASSAS SORU]',
        expect: {
          toolExpected: true,
        },
      },
    ],
  },
  {
    id: 4,
    category: 'memory',
    name: 'Ornek — cok turn, profil hatirlanmali',
    turns: [
      {
        user: '[ILK MESAJ — profil bilgisi icerir]',
        expect: { mustNotContain: NO_EM_DASH },
      },
      {
        user: '[IKINCI MESAJ — onceki baglama dayanir]',
        expect: {
          mustNotContain: NO_EM_DASH,
        },
      },
    ],
  },
];
