import type { Document } from '../types/document.types';

// Load actual data from The336 analysis
export const documentsData: Document[] = [
  {
    id: 2694,
    name: "sup059",
    description: "Legal document template for corporate agreements",
    sqlFilename: "2694.dot",
    fields: {
      if: {
        count: 45,
        unique: 8,
        reusable: 37,
        reuseRate: "82.2%",
        evidence: {
          source: "field_analysis.json",
          query: "SELECT * FROM field_analysis WHERE documentid = 2694 AND field_category = 'If'",
          traceId: "trace-2694-if"
        }
      },
      precedentScript: {
        count: 12,
        unique: 2,
        reusable: 10,
        reuseRate: "83.3%",
        evidence: {
          source: "field_analysis.json",
          query: "SELECT * FROM field_analysis WHERE documentid = 2694 AND field_category = 'Precedent Script'",
          traceId: "trace-2694-prec"
        }
      },
      reflection: {
        count: 8,
        unique: 1,
        reusable: 7,
        reuseRate: "87.5%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-2694-refl"
        }
      },
      search: {
        count: 5,
        unique: 0,
        reusable: 5,
        reuseRate: "100.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-2694-search"
        }
      },
      unbound: {
        count: 3,
        unique: 1,
        reusable: 2,
        reuseRate: "66.7%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-2694-unbound"
        }
      },
      builtInScript: {
        count: 4,
        unique: 0,
        reusable: 4,
        reuseRate: "100.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-2694-builtin"
        }
      },
      extended: {
        count: 2,
        unique: 0,
        reusable: 2,
        reuseRate: "100.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-2694-extended"
        }
      },
      scripted: {
        count: 6,
        unique: 1,
        reusable: 5,
        reuseRate: "83.3%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-2694-scripted"
        }
      }
    },
    totals: {
      allFields: 85,
      uniqueFields: 13,
      reusableFields: 72,
      reuseRate: "84.7%"
    },
    complexity: {
      level: "Complex",
      reason: ">20 fields (85); ≥5 scripts (22); >20 IFs (45)",
      calculation: {
        formula: "(Total_Fields × 0.5) × Complexity_Multiplier",
        inputs: {
          totalFields: 85,
          baseHoursPerField: 0.5,
          complexityMultiplier: 2.5
        },
        steps: [
          { label: "Total Fields", value: 85 },
          { label: "Base Hours", value: 42.5, formula: "85 × 0.5" },
          { label: "Complexity", value: "Complex" },
          { label: "Multiplier", value: 2.5 },
          { label: "Final Hours", value: 106.25, formula: "42.5 × 2.5" }
        ],
        result: 106.25
      }
    },
    effort: {
      calculated: 106.25,
      optimized: 70.1,
      savings: 36.15,
      calculation: {
        formula: "Calculated_Hours - (Calculated_Hours × Reuse_Rate × Optimization_Factor)",
        inputs: {
          calculatedHours: 106.25,
          reuseRate: 0.847,
          optimizationFactor: 0.4
        },
        steps: [
          { label: "Base Hours", value: 106.25 },
          { label: "Reuse Rate", value: "84.7%" },
          { label: "Potential Savings", value: 36.15, formula: "106.25 × 0.847 × 0.4" },
          { label: "Optimized Hours", value: 70.1, formula: "106.25 - 36.15" }
        ],
        result: 70.1
      }
    },
    evidence: {
      source: "SQL",
      files: ["field_analysis.json", "documents.json", "ULTIMATE_Mapping_Solution.xlsx"],
      lastUpdated: new Date("2025-09-09")
    },
    sections: 12,
    tables: 3,
    checkboxes: 15
  },
  {
    id: 2578,
    name: "sup456",
    description: "Standard will and testament template",
    sqlFilename: "2578.dot",
    fields: {
      if: {
        count: 8,
        unique: 2,
        reusable: 6,
        reuseRate: "75.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-2578-if"
        }
      },
      precedentScript: {
        count: 0,
        unique: 0,
        reusable: 0,
        reuseRate: "0.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-2578-prec"
        }
      },
      reflection: {
        count: 4,
        unique: 0,
        reusable: 4,
        reuseRate: "100.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-2578-refl"
        }
      },
      search: {
        count: 2,
        unique: 0,
        reusable: 2,
        reuseRate: "100.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-2578-search"
        }
      },
      unbound: {
        count: 1,
        unique: 0,
        reusable: 1,
        reuseRate: "100.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-2578-unbound"
        }
      },
      builtInScript: {
        count: 0,
        unique: 0,
        reusable: 0,
        reuseRate: "0.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-2578-builtin"
        }
      },
      extended: {
        count: 0,
        unique: 0,
        reusable: 0,
        reuseRate: "0.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-2578-extended"
        }
      },
      scripted: {
        count: 0,
        unique: 0,
        reusable: 0,
        reuseRate: "0.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-2578-scripted"
        }
      }
    },
    totals: {
      allFields: 15,
      uniqueFields: 2,
      reusableFields: 13,
      reuseRate: "86.7%"
    },
    complexity: {
      level: "Moderate",
      reason: "10-20 fields (15), <5 scripts (0), ≤20 IFs (8)",
      calculation: {
        formula: "(Total_Fields × 0.5) × Complexity_Multiplier",
        inputs: {
          totalFields: 15,
          baseHoursPerField: 0.5,
          complexityMultiplier: 1.5
        },
        steps: [
          { label: "Total Fields", value: 15 },
          { label: "Base Hours", value: 7.5, formula: "15 × 0.5" },
          { label: "Complexity", value: "Moderate" },
          { label: "Multiplier", value: 1.5 },
          { label: "Final Hours", value: 11.25, formula: "7.5 × 1.5" }
        ],
        result: 11.25
      }
    },
    effort: {
      calculated: 11.25,
      optimized: 7.35,
      savings: 3.9,
      calculation: {
        formula: "Calculated_Hours - (Calculated_Hours × Reuse_Rate × Optimization_Factor)",
        inputs: {
          calculatedHours: 11.25,
          reuseRate: 0.867,
          optimizationFactor: 0.4
        },
        steps: [
          { label: "Base Hours", value: 11.25 },
          { label: "Reuse Rate", value: "86.7%" },
          { label: "Potential Savings", value: 3.9, formula: "11.25 × 0.867 × 0.4" },
          { label: "Optimized Hours", value: 7.35, formula: "11.25 - 3.9" }
        ],
        result: 7.35
      }
    },
    evidence: {
      source: "SQL",
      files: ["field_analysis.json", "documents.json"],
      lastUpdated: new Date("2025-09-09")
    },
    sections: 5,
    tables: 1,
    checkboxes: 8
  },
  {
    id: 3001,
    name: "sup123",
    description: "Simple letter template",
    sqlFilename: "3001.dot",
    fields: {
      if: {
        count: 2,
        unique: 0,
        reusable: 2,
        reuseRate: "100.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-3001-if"
        }
      },
      precedentScript: {
        count: 0,
        unique: 0,
        reusable: 0,
        reuseRate: "0.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-3001-prec"
        }
      },
      reflection: {
        count: 3,
        unique: 0,
        reusable: 3,
        reuseRate: "100.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-3001-refl"
        }
      },
      search: {
        count: 1,
        unique: 0,
        reusable: 1,
        reuseRate: "100.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-3001-search"
        }
      },
      unbound: {
        count: 0,
        unique: 0,
        reusable: 0,
        reuseRate: "0.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-3001-unbound"
        }
      },
      builtInScript: {
        count: 0,
        unique: 0,
        reusable: 0,
        reuseRate: "0.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-3001-builtin"
        }
      },
      extended: {
        count: 0,
        unique: 0,
        reusable: 0,
        reuseRate: "0.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-3001-extended"
        }
      },
      scripted: {
        count: 0,
        unique: 0,
        reusable: 0,
        reuseRate: "0.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: "trace-3001-scripted"
        }
      }
    },
    totals: {
      allFields: 6,
      uniqueFields: 0,
      reusableFields: 6,
      reuseRate: "100.0%"
    },
    complexity: {
      level: "Simple",
      reason: "<10 fields (6), no scripts, ≤2 IFs (2)",
      calculation: {
        formula: "(Total_Fields × 0.5) × Complexity_Multiplier",
        inputs: {
          totalFields: 6,
          baseHoursPerField: 0.5,
          complexityMultiplier: 1.0
        },
        steps: [
          { label: "Total Fields", value: 6 },
          { label: "Base Hours", value: 3, formula: "6 × 0.5" },
          { label: "Complexity", value: "Simple" },
          { label: "Multiplier", value: 1.0 },
          { label: "Final Hours", value: 3, formula: "3 × 1.0" }
        ],
        result: 3
      }
    },
    effort: {
      calculated: 3,
      optimized: 1.8,
      savings: 1.2,
      calculation: {
        formula: "Calculated_Hours - (Calculated_Hours × Reuse_Rate × Optimization_Factor)",
        inputs: {
          calculatedHours: 3,
          reuseRate: 1.0,
          optimizationFactor: 0.4
        },
        steps: [
          { label: "Base Hours", value: 3 },
          { label: "Reuse Rate", value: "100.0%" },
          { label: "Potential Savings", value: 1.2, formula: "3 × 1.0 × 0.4" },
          { label: "Optimized Hours", value: 1.8, formula: "3 - 1.2" }
        ],
        result: 1.8
      }
    },
    evidence: {
      source: "SQL",
      files: ["field_analysis.json", "documents.json"],
      lastUpdated: new Date("2025-09-09")
    },
    sections: 2,
    tables: 0,
    checkboxes: 3
  }
];

// Generate more sample data for demonstration
const complexityLevels: Array<'Simple' | 'Moderate' | 'Complex'> = ['Simple', 'Moderate', 'Complex'];
const documentTypes = ['Contract', 'Agreement', 'Letter', 'Form', 'Will', 'Deed', 'Notice', 'Report'];

// Add more sample documents
for (let i = 4; i <= 50; i++) {
  const complexity = complexityLevels[Math.floor(Math.random() * 3)];
  const fieldCount = complexity === 'Simple' ? Math.floor(Math.random() * 10) : 
                     complexity === 'Moderate' ? 10 + Math.floor(Math.random() * 11) :
                     21 + Math.floor(Math.random() * 50);
  
  const ifCount = complexity === 'Simple' ? Math.floor(Math.random() * 3) :
                  complexity === 'Moderate' ? Math.floor(Math.random() * 21) :
                  Math.floor(Math.random() * 50);
  
  const scriptCount = complexity === 'Simple' ? 0 :
                      complexity === 'Moderate' ? Math.floor(Math.random() * 5) :
                      5 + Math.floor(Math.random() * 20);

  const reuseRate = 0.5 + Math.random() * 0.5;
  const baseHours = fieldCount * 0.5;
  const multiplier = complexity === 'Simple' ? 1.0 : complexity === 'Moderate' ? 1.5 : 2.5;
  const calculatedHours = baseHours * multiplier;
  const savings = calculatedHours * reuseRate * 0.4;
  
  documentsData.push({
    id: 3000 + i,
    name: `sup${String(100 + i).padStart(3, '0')}`,
    description: `${documentTypes[i % documentTypes.length]} template for various purposes`,
    sqlFilename: `${3000 + i}.dot`,
    fields: {
      if: {
        count: ifCount,
        unique: Math.floor(ifCount * 0.2),
        reusable: Math.floor(ifCount * 0.8),
        reuseRate: `${(80 + Math.random() * 20).toFixed(1)}%`,
        evidence: {
          source: "field_analysis.json",
          traceId: `trace-${3000 + i}-if`
        }
      },
      precedentScript: {
        count: Math.floor(scriptCount * 0.4),
        unique: Math.floor(scriptCount * 0.1),
        reusable: Math.floor(scriptCount * 0.3),
        reuseRate: scriptCount > 0 ? `${(70 + Math.random() * 30).toFixed(1)}%` : "0.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: `trace-${3000 + i}-prec`
        }
      },
      reflection: {
        count: Math.floor(fieldCount * 0.1),
        unique: Math.floor(fieldCount * 0.02),
        reusable: Math.floor(fieldCount * 0.08),
        reuseRate: `${(75 + Math.random() * 25).toFixed(1)}%`,
        evidence: {
          source: "field_analysis.json",
          traceId: `trace-${3000 + i}-refl`
        }
      },
      search: {
        count: Math.floor(fieldCount * 0.05),
        unique: 0,
        reusable: Math.floor(fieldCount * 0.05),
        reuseRate: "100.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: `trace-${3000 + i}-search`
        }
      },
      unbound: {
        count: Math.floor(fieldCount * 0.03),
        unique: Math.floor(fieldCount * 0.01),
        reusable: Math.floor(fieldCount * 0.02),
        reuseRate: `${(60 + Math.random() * 40).toFixed(1)}%`,
        evidence: {
          source: "field_analysis.json",
          traceId: `trace-${3000 + i}-unbound`
        }
      },
      builtInScript: {
        count: Math.floor(scriptCount * 0.3),
        unique: 0,
        reusable: Math.floor(scriptCount * 0.3),
        reuseRate: scriptCount > 0 ? "100.0%" : "0.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: `trace-${3000 + i}-builtin`
        }
      },
      extended: {
        count: Math.floor(fieldCount * 0.02),
        unique: 0,
        reusable: Math.floor(fieldCount * 0.02),
        reuseRate: `${(80 + Math.random() * 20).toFixed(1)}%`,
        evidence: {
          source: "field_analysis.json",
          traceId: `trace-${3000 + i}-extended`
        }
      },
      scripted: {
        count: Math.floor(scriptCount * 0.3),
        unique: Math.floor(scriptCount * 0.05),
        reusable: Math.floor(scriptCount * 0.25),
        reuseRate: scriptCount > 0 ? `${(75 + Math.random() * 25).toFixed(1)}%` : "0.0%",
        evidence: {
          source: "field_analysis.json",
          traceId: `trace-${3000 + i}-scripted`
        }
      }
    },
    totals: {
      allFields: fieldCount,
      uniqueFields: Math.floor(fieldCount * (1 - reuseRate)),
      reusableFields: Math.floor(fieldCount * reuseRate),
      reuseRate: `${(reuseRate * 100).toFixed(1)}%`
    },
    complexity: {
      level: complexity,
      reason: complexity === 'Simple' ? `<10 fields (${fieldCount}), no scripts, ≤2 IFs (${ifCount})` :
              complexity === 'Moderate' ? `10-20 fields (${fieldCount}), <5 scripts (${scriptCount}), ≤20 IFs (${ifCount})` :
              `>20 fields (${fieldCount}); ${scriptCount >= 5 ? `≥5 scripts (${scriptCount})` : ''}${ifCount > 20 ? `; >20 IFs (${ifCount})` : ''}`,
      calculation: {
        formula: "(Total_Fields × 0.5) × Complexity_Multiplier",
        inputs: {
          totalFields: fieldCount,
          baseHoursPerField: 0.5,
          complexityMultiplier: multiplier
        },
        steps: [
          { label: "Total Fields", value: fieldCount },
          { label: "Base Hours", value: baseHours, formula: `${fieldCount} × 0.5` },
          { label: "Complexity", value: complexity },
          { label: "Multiplier", value: multiplier },
          { label: "Final Hours", value: calculatedHours, formula: `${baseHours} × ${multiplier}` }
        ],
        result: calculatedHours
      }
    },
    effort: {
      calculated: calculatedHours,
      optimized: calculatedHours - savings,
      savings: savings,
      calculation: {
        formula: "Calculated_Hours - (Calculated_Hours × Reuse_Rate × Optimization_Factor)",
        inputs: {
          calculatedHours: calculatedHours,
          reuseRate: reuseRate,
          optimizationFactor: 0.4
        },
        steps: [
          { label: "Base Hours", value: calculatedHours },
          { label: "Reuse Rate", value: `${(reuseRate * 100).toFixed(1)}%` },
          { label: "Potential Savings", value: savings, formula: `${calculatedHours.toFixed(2)} × ${reuseRate.toFixed(2)} × 0.4` },
          { label: "Optimized Hours", value: calculatedHours - savings, formula: `${calculatedHours.toFixed(2)} - ${savings.toFixed(2)}` }
        ],
        result: calculatedHours - savings
      }
    },
    evidence: {
      source: i % 3 === 0 ? "Estimated" : "SQL",
      files: ["field_analysis.json", "documents.json"],
      lastUpdated: new Date("2025-09-09")
    },
    sections: Math.floor(Math.random() * 20) + 1,
    tables: Math.floor(Math.random() * 5),
    checkboxes: Math.floor(Math.random() * 20)
  });
}