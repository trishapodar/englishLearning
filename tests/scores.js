// ══════════════════════════════════════════════════════════════
// SCORE REGISTRY
// To log a student's test score, append an object to this array.
// Fields:
//   date      — Date of the test ("DD MMM YYYY" or "YYYY-MM-DD")
//   student   — Name of the student
//   class     — Class level (e.g., "Class 5", "Class 9")
//   subject   — e.g. "Science", "Mathematics"
//   topic     — Main topic or chapter (used for progress tracking)
//   score     — Marks obtained
//   total     — Maximum possible marks
// ══════════════════════════════════════════════════════════════

const SCORES = [
  // Example Baseline Data
  { date: "01 Mar 2026", student: "Rohan", class: "Class 5", subject: "Science", topic: "Plants", score: 14, total: 20 },
  { date: "15 Mar 2026", student: "Rohan", class: "Class 5", subject: "Science", topic: "Plants", score: 16, total: 20 },
  { date: "10 Apr 2026", student: "Rohan", class: "Class 5", subject: "Science", topic: "Plants", score: 18, total: 20 },
  { date: "12 Apr 2026", student: "Rohan", class: "Class 5", subject: "Science", topic: "Plants", score: 19, total: 20 },
  
  { date: "02 Apr 2026", student: "Meera", class: "Class 9", subject: "Science", topic: "Cell Biology", score: 28, total: 40 },
  { date: "11 Apr 2026", student: "Meera", class: "Class 9", subject: "Science", topic: "Cell Biology", score: 34, total: 40 },
  { date: "12 Apr 2026", student: "Meera", class: "Class 9", subject: "Science", topic: "Cell Biology", score: 38, total: 40 },

  { date: "05 Apr 2026", student: "Kavya", class: "Class 4", subject: "Mathematics", topic: "Geometry", score: 12, total: 20 },
  { date: "09 Apr 2026", student: "Kavya", class: "Class 4", subject: "Mathematics", topic: "Geometry", score: 17, total: 20 },
];
