// ══════════════════════════════════════════════════════════════
// SCORE REGISTRY
// To log a student's test score, append an object to this array.
// Fields:
//   dateAttempted — Date when the test was actually taken ("DD MMM YYYY")
//   student       — Name of the student
//   class         — Class level (e.g., "Class 5", "Class 9")
//   subject       — e.g. "Science", "Mathematics"
//   topic         — Main topic or chapter (used for progress tracking)
//   testFile      — Filename or URL of the exact test attempt
//   score         — Marks obtained
//   total         — Maximum possible marks
// ══════════════════════════════════════════════════════════════

const SCORES = [
  // Example Baseline Data
  { dateAttempted: "01 Mar 2026", student: "Rohan", class: "Class 5", subject: "Science", topic: "Plants", testFile: "class5_science_plants_20260410.html", score: 14, total: 20 },
  { dateAttempted: "15 Mar 2026", student: "Rohan", class: "Class 5", subject: "Science", topic: "Plants", testFile: "class5_science_plants_20260410.html", score: 16, total: 20 },
  { dateAttempted: "10 Apr 2026", student: "Rohan", class: "Class 5", subject: "Science", topic: "Plants", testFile: "class5_science_plants_20260410.html", score: 18, total: 20 },
  { dateAttempted: "12 Apr 2026", student: "Rohan", class: "Class 5", subject: "Science", topic: "Plants", testFile: "class5_science_plants_agriculture_20260412.html", score: 19, total: 20 },

  { dateAttempted: "02 Apr 2026", student: "Meera", class: "Class 9", subject: "Science", topic: "Cell Biology", testFile: "class9_science_cell_20260411.html", score: 28, total: 40 },
  { dateAttempted: "11 Apr 2026", student: "Meera", class: "Class 9", subject: "Science", topic: "Cell Biology", testFile: "class9_science_cell_20260411.html", score: 34, total: 40 },
  { dateAttempted: "12 Apr 2026", student: "Meera", class: "Class 9", subject: "Science", topic: "Cell Biology", testFile: "class9_science_cell_20260412.html", score: 38, total: 40 },

  { dateAttempted: "05 Apr 2026", student: "Kavya", class: "Class 4", subject: "Mathematics", topic: "Geometry", testFile: "class4_mathematics_geometry_20260409.html", score: 12, total: 20 },
  { dateAttempted: "09 Apr 2026", student: "Kavya", class: "Class 4", subject: "Mathematics", topic: "Geometry", testFile: "class4_mathematics_geometry_20260409.html", score: 17, total: 20 },
];
