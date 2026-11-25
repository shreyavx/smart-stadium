/* ==========================================================================
   SMART STADIUM – UNIVERSAL SMART VENUE SIMULATOR (FRONTEND ONLY)
   --------------------------------------------------------------------------
   Organized into two clean parts:
   1. VENUE_PRESETS: Distinct 2D SVG layouts and initial crowd data for 5 venues
   2. SIMULATOR ENGINE: Reusable SVG renderer, zone interactions, and live loop
   ========================================================================== */

// ==========================================================================
// 1. VENUE PRESETS (SEPARATE LAYOUT & DATA DEFINITIONS)
// ==========================================================================

const VENUE_PRESETS = {
    "sports-stadium": {
        name: "Sports Stadium",
        subtitle: "Cricket / Football Ground • Central pitch, 4 stands & corner concourses",
        architecture: [
            // Outer bowl wall
            { tag: "ellipse", attrs: { cx: 400, cy: 250, rx: 382, ry: 228, fill: "#0f172a", stroke: "#334155", "stroke-width": 2.5 } },
            // Concourse ring track
            { tag: "ellipse", attrs: { cx: 400, cy: 250, rx: 340, ry: 196, fill: "none", stroke: "#1e293b", "stroke-width": 16 } },
            // Central Football/Cricket Turf Pitch
            { tag: "rect", attrs: { x: 262, y: 158, width: 276, height: 184, rx: 22, fill: "#064e3b", stroke: "#10b981", "stroke-width": 2 } },
            { tag: "line", attrs: { x1: 400, y1: 158, x2: 400, y2: 342, stroke: "rgba(255,255,255,0.45)", "stroke-width": 1.5 } },
            { tag: "circle", attrs: { cx: 400, cy: 250, r: 34, fill: "none", stroke: "rgba(255,255,255,0.45)", "stroke-width": 1.5 } },
            { tag: "rect", attrs: { x: 262, y: 204, width: 32, height: 92, fill: "none", stroke: "rgba(255,255,255,0.4)", "stroke-width": 1.5 } },
            { tag: "rect", attrs: { x: 506, y: 204, width: 32, height: 92, fill: "none", stroke: "rgba(255,255,255,0.4)", "stroke-width": 1.5 } },
            { tag: "text", attrs: { x: 400, y: 254, "text-anchor": "middle", fill: "#a7f3d0", "font-size": 12, "font-weight": 700, "letter-spacing": 1 }, text: "MAIN PLAYING FIELD" }
        ],
        zones: [
            {
                id: "Z1", name: "North Stand", description: "Main covered north seating tier facing the pitch.",
                initialCrowd: 4200, maxCapacity: 6000, bottleneckBias: 1.1,
                shapeType: "rect", shapeAttrs: { x: 252, y: 54, width: 296, height: 82, rx: 14 },
                labelPos: { x: 400, y: 84 }
            },
            {
                id: "Z2", name: "South Stand", description: "Family and general seating stand on the south side.",
                initialCrowd: 2800, maxCapacity: 6000, bottleneckBias: 0.7,
                shapeType: "rect", shapeAttrs: { x: 252, y: 364, width: 296, height: 82, rx: 14 },
                labelPos: { x: 400, y: 394 }
            },
            {
                id: "Z3", name: "West Stand", description: "West pavilion seating block with media boxes.",
                initialCrowd: 2150, maxCapacity: 4000, bottleneckBias: 0.85,
                shapeType: "rect", shapeAttrs: { x: 132, y: 152, width: 108, height: 196, rx: 14 },
                labelPos: { x: 186, y: 238 }
            },
            {
                id: "Z4", name: "East Stand", description: "East supporter stand adjacent to Gate B concourse.",
                initialCrowd: 3250, maxCapacity: 4000, bottleneckBias: 1.35,
                shapeType: "rect", shapeAttrs: { x: 560, y: 152, width: 108, height: 196, rx: 14 },
                labelPos: { x: 614, y: 238 }
            },
            {
                id: "Z5", name: "NW Gate A Concourse", description: "Primary northwest entry security and ticket check.",
                initialCrowd: 1450, maxCapacity: 2500, bottleneckBias: 0.9,
                shapeType: "rect", shapeAttrs: { x: 64, y: 46, width: 162, height: 84, rx: 14 },
                labelPos: { x: 145, y: 78 }
            },
            {
                id: "Z6", name: "NE Gate B Concourse", description: "High-traffic northeast concourse near concessions.",
                initialCrowd: 2280, maxCapacity: 2500, bottleneckBias: 1.45,
                shapeType: "rect", shapeAttrs: { x: 574, y: 46, width: 162, height: 84, rx: 14 },
                labelPos: { x: 655, y: 78 }
            },
            {
                id: "Z7", name: "SW Gate C Exit Hub", description: "Southwest dispersal corridor and transit walkway.",
                initialCrowd: 980, maxCapacity: 2500, bottleneckBias: 0.65,
                shapeType: "rect", shapeAttrs: { x: 64, y: 370, width: 162, height: 84, rx: 14 },
                labelPos: { x: 145, y: 402 }
            },
            {
                id: "Z8", name: "SE Gate D Exit Hub", description: "Southeast overflow exit and shuttle staging area.",
                initialCrowd: 1120, maxCapacity: 2500, bottleneckBias: 0.75,
                shapeType: "rect", shapeAttrs: { x: 574, y: 370, width: 162, height: 84, rx: 14 },
                labelPos: { x: 655, y: 402 }
            }
        ],
        connections: [
            ["Z5", "Z1"], ["Z5", "Z3"],
            ["Z6", "Z1"], ["Z6", "Z4"],
            ["Z4", "Z8"], ["Z3", "Z7"],
            ["Z2", "Z7"], ["Z2", "Z8"]
        ],
        gates: [
            { label: "Gate A", type: "entry", x: 44, y: 72 },
            { label: "Gate B", type: "entry", x: 756, y: 72 },
            { label: "Gate C", type: "exit", x: 44, y: 428 },
            { label: "Gate D", type: "exit", x: 756, y: 428 },
            { label: "EM-N", type: "emergency", x: 400, y: 24 },
            { label: "EM-S", type: "emergency", x: 400, y: 476 }
        ],
        facilityPositions: {
            food: { x: 138, y: 8 },
            entry: { x: 650, y: 8 },
            washrooms: { x: 660, y: 140 },
            medical: { x: 8, y: 320 },
            emergency: { x: 326, y: 458 },
            merchandise: { x: 282, y: 8 },
            parking: { x: 8, y: 175 },
            security: { x: 8, y: 8 }
        }
    },

    "outdoor-concert": {
        name: "Outdoor Concert Ground",
        subtitle: "Open-Air Festival Lawn • Main stage, front pit, VIP deck & food village",
        architecture: [
            // Open festival perimeter fence
            { tag: "rect", attrs: { x: 28, y: 28, width: 744, height: 444, rx: 18, fill: "#0b1324", stroke: "#334155", "stroke-width": 2.5, "stroke-dasharray": "8 4" } },
            // Backstage & Main Stage on Left
            { tag: "rect", attrs: { x: 46, y: 108, width: 104, height: 284, rx: 10, fill: "#1e1b4b", stroke: "#818cf8", "stroke-width": 2.5 } },
            { tag: "rect", attrs: { x: 138, y: 120, width: 16, height: 48, rx: 4, fill: "#4f46e5" } },
            { tag: "rect", attrs: { x: 138, y: 332, width: 16, height: 48, rx: 4, fill: "#4f46e5" } },
            { tag: "text", attrs: { x: 96, y: 245, "text-anchor": "middle", fill: "#c7d2fe", "font-size": 13, "font-weight": 700 }, text: "MAIN" },
            { tag: "text", attrs: { x: 96, y: 264, "text-anchor": "middle", fill: "#c7d2fe", "font-size": 13, "font-weight": 700 }, text: "STAGE" },
            // Sound & Lighting Tower in middle of lawn
            { tag: "rect", attrs: { x: 410, y: 274, width: 34, height: 24, rx: 4, fill: "#1e293b", stroke: "#64748b", "stroke-width": 1.5 } },
            { tag: "text", attrs: { x: 427, y: 290, "text-anchor": "middle", fill: "#94a3b8", "font-size": 8, "font-weight": 700 }, text: "FOH" }
        ],
        zones: [
            {
                id: "Z1", name: "Front Pit (Golden Circle)", description: "High-density standing area directly in front of the main stage.",
                initialCrowd: 3180, maxCapacity: 3500, bottleneckBias: 1.5,
                shapeType: "rect", shapeAttrs: { x: 172, y: 112, width: 130, height: 276, rx: 16 },
                labelPos: { x: 237, y: 236 }
            },
            {
                id: "Z2", name: "VIP Viewing Deck", description: "Elevated VIP terrace with dedicated bar and side-stage sightline.",
                initialCrowd: 920, maxCapacity: 1500, bottleneckBias: 0.75,
                shapeType: "rect", shapeAttrs: { x: 326, y: 48, width: 204, height: 90, rx: 12 },
                labelPos: { x: 428, y: 82 }
            },
            {
                id: "Z3", name: "General Lawn North", description: "North open standing lawn facing the main stage screens.",
                initialCrowd: 3650, maxCapacity: 5000, bottleneckBias: 1.15,
                shapeType: "rect", shapeAttrs: { x: 326, y: 154, width: 204, height: 114, rx: 12 },
                labelPos: { x: 428, y: 200 }
            },
            {
                id: "Z4", name: "General Lawn South", description: "South general admission lawn with open seating blankets.",
                initialCrowd: 2400, maxCapacity: 5000, bottleneckBias: 0.9,
                shapeType: "rect", shapeAttrs: { x: 326, y: 306, width: 204, height: 138, rx: 12 },
                labelPos: { x: 428, y: 364 }
            },
            {
                id: "Z5", name: "Food & Beverage Village", description: "Outdoor food trucks, water refill stations, and picnic area.",
                initialCrowd: 1920, maxCapacity: 2400, bottleneckBias: 1.25,
                shapeType: "rect", shapeAttrs: { x: 554, y: 48, width: 194, height: 120, rx: 12 },
                labelPos: { x: 651, y: 98 }
            },
            {
                id: "Z6", name: "East Main Entry Plaza", description: "Ticket scanning, bag check, and primary arrival funnel.",
                initialCrowd: 1850, maxCapacity: 2500, bottleneckBias: 1.2,
                shapeType: "rect", shapeAttrs: { x: 554, y: 188, width: 194, height: 124, rx: 12 },
                labelPos: { x: 651, y: 240 }
            },
            {
                id: "Z7", name: "South Merch & Exit", description: "Merchandise tents and southern festival egress path.",
                initialCrowd: 960, maxCapacity: 2200, bottleneckBias: 0.65,
                shapeType: "rect", shapeAttrs: { x: 554, y: 332, width: 194, height: 112, rx: 12 },
                labelPos: { x: 651, y: 378 }
            }
        ],
        connections: [
            ["Z6", "Z5"], ["Z6", "Z3"], ["Z6", "Z7"],
            ["Z5", "Z2"], ["Z3", "Z1"], ["Z4", "Z1"],
            ["Z4", "Z7"], ["Z2", "Z1"]
        ],
        gates: [
            { label: "Main In", type: "entry", x: 766, y: 250 },
            { label: "VIP In", type: "entry", x: 428, y: 24 },
            { label: "South Out", type: "exit", x: 651, y: 472 },
            { label: "EM-NW", type: "emergency", x: 98, y: 38 },
            { label: "EM-SW", type: "emergency", x: 98, y: 462 }
        ],
        facilityPositions: {
            food: { x: 620, y: 8 },
            entry: { x: 650, y: 178 },
            washrooms: { x: 650, y: 306 },
            medical: { x: 12, y: 302 },
            emergency: { x: 146, y: 438 },
            merchandise: { x: 138, y: 8 },
            parking: { x: 12, y: 178 },
            security: { x: 8, y: 8 }
        }
    },

    "indoor-arena": {
        name: "Indoor Concert Arena",
        subtitle: "Enclosed Multi-Tier Arena • 360° central stage, radial aisles & lobbies",
        architecture: [
            // Thick enclosed arena shell
            { tag: "rect", attrs: { x: 46, y: 32, width: 708, height: 436, rx: 52, fill: "#0f172a", stroke: "#475569", "stroke-width": 4 } },
            // Radial walking aisle guides
            { tag: "line", attrs: { x1: 148, y1: 136, x2: 265, y2: 185, stroke: "#334155", "stroke-width": 4 } },
            { tag: "line", attrs: { x1: 652, y1: 136, x2: 535, y2: 185, stroke: "#334155", "stroke-width": 4 } },
            { tag: "line", attrs: { x1: 148, y1: 364, x2: 265, y2: 315, stroke: "#334155", "stroke-width": 4 } },
            { tag: "line", attrs: { x1: 652, y1: 364, x2: 535, y2: 315, stroke: "#334155", "stroke-width": 4 } }
        ],
        overlayArchitecture: [
            // Central 360-degree stage rendered above floor zone
            { tag: "rect", attrs: { x: 344, y: 204, width: 112, height: 92, rx: 14, fill: "#312e81", stroke: "#818cf8", "stroke-width": 2.5, "pointer-events": "none" } },
            { tag: "text", attrs: { x: 400, y: 247, "text-anchor": "middle", fill: "#e0e7ff", "font-size": 11, "font-weight": 700, "pointer-events": "none" }, text: "CENTER" },
            { tag: "text", attrs: { x: 400, y: 262, "text-anchor": "middle", fill: "#e0e7ff", "font-size": 11, "font-weight": 700, "pointer-events": "none" }, text: "STAGE" }
        ],
        zones: [
            {
                id: "Z1", name: "Arena Floor Standing", description: "Standing pit surrounding the central 360° event stage.",
                initialCrowd: 2420, maxCapacity: 2800, bottleneckBias: 1.4,
                shapeType: "rect", shapeAttrs: { x: 264, y: 146, width: 272, height: 208, rx: 22 },
                labelPos: { x: 400, y: 170 }
            },
            {
                id: "Z2", name: "North Tier Seating", description: "Upper and lower north bowl seated sections.",
                initialCrowd: 1850, maxCapacity: 3200, bottleneckBias: 0.9,
                shapeType: "rect", shapeAttrs: { x: 215, y: 52, width: 370, height: 74, rx: 12 },
                labelPos: { x: 400, y: 79 }
            },
            {
                id: "Z3", name: "South Tier Seating", description: "South bowl seated sections near exit stairwells.",
                initialCrowd: 1480, maxCapacity: 3200, bottleneckBias: 0.75,
                shapeType: "rect", shapeAttrs: { x: 215, y: 374, width: 370, height: 74, rx: 12 },
                labelPos: { x: 400, y: 401 }
            },
            {
                id: "Z4", name: "West Bowl Seating", description: "West curved seating block off the main security lobby.",
                initialCrowd: 1620, maxCapacity: 2200, bottleneckBias: 1.05,
                shapeType: "rect", shapeAttrs: { x: 154, y: 146, width: 92, height: 208, rx: 12 },
                labelPos: { x: 200, y: 238 }
            },
            {
                id: "Z5", name: "East Bowl Seating", description: "East seating block connecting to the indoor atrium.",
                initialCrowd: 1940, maxCapacity: 2200, bottleneckBias: 1.25,
                shapeType: "rect", shapeAttrs: { x: 554, y: 146, width: 92, height: 208, rx: 12 },
                labelPos: { x: 600, y: 238 }
            },
            {
                id: "Z6", name: "West Lobby & Screening", description: "Enclosed indoor security turnstiles and ticket lobby.",
                initialCrowd: 1120, maxCapacity: 1600, bottleneckBias: 1.1,
                shapeType: "rect", shapeAttrs: { x: 68, y: 108, width: 70, height: 284, rx: 12 },
                labelPos: { x: 103, y: 238 }
            },
            {
                id: "Z7", name: "East Atrium Concourse", description: "Main indoor concourse with escalators and restrooms.",
                initialCrowd: 1490, maxCapacity: 1600, bottleneckBias: 1.45,
                shapeType: "rect", shapeAttrs: { x: 662, y: 108, width: 70, height: 284, rx: 12 },
                labelPos: { x: 697, y: 238 }
            }
        ],
        connections: [
            ["Z6", "Z4"], ["Z6", "Z2"], ["Z4", "Z1"],
            ["Z7", "Z5"], ["Z7", "Z3"], ["Z5", "Z1"],
            ["Z1", "Z2"], ["Z1", "Z3"]
        ],
        gates: [
            { label: "W-Entry", type: "entry", x: 34, y: 250 },
            { label: "E-Entry", type: "entry", x: 766, y: 250 },
            { label: "N-Exit", type: "exit", x: 400, y: 22 },
            { label: "S-Exit", type: "exit", x: 400, y: 478 },
            { label: "EM-1", type: "emergency", x: 96, y: 56 },
            { label: "EM-2", type: "emergency", x: 704, y: 56 },
            { label: "EM-3", type: "emergency", x: 96, y: 444 },
            { label: "EM-4", type: "emergency", x: 704, y: 444 }
        ],
        facilityPositions: {
            food: { x: 138, y: 8 },
            entry: { x: 650, y: 8 },
            washrooms: { x: 660, y: 148 },
            medical: { x: 8, y: 310 },
            emergency: { x: 326, y: 458 },
            merchandise: { x: 282, y: 8 },
            parking: { x: 8, y: 148 },
            security: { x: 8, y: 8 }
        }
    },

    "auditorium": {
        name: "Auditorium",
        subtitle: "Seated Theater Hall • Proscenium stage, central/side aisles & foyer",
        architecture: [
            // Auditorium walls
            { tag: "rect", attrs: { x: 68, y: 26, width: 664, height: 448, rx: 16, fill: "#0f172a", stroke: "#334155", "stroke-width": 2.5 } },
            // Proscenium Main Stage
            { tag: "rect", attrs: { x: 185, y: 42, width: 430, height: 78, rx: 10, fill: "#1e1b4b", stroke: "#818cf8", "stroke-width": 2.5 } },
            { tag: "path", attrs: { d: "M 220 120 Q 400 144 580 120", fill: "#312e81", stroke: "#6366f1", "stroke-width": 1.5 } },
            { tag: "text", attrs: { x: 400, y: 86, "text-anchor": "middle", fill: "#e0e7ff", "font-size": 14, "font-weight": 700, "letter-spacing": 1.5 }, text: "PROSCENIUM STAGE" },
            // Central & Side Walking Aisles
            { tag: "rect", attrs: { x: 382, y: 146, width: 36, height: 244, rx: 4, fill: "#1e293b", stroke: "#475569", "stroke-width": 1 } },
            { tag: "rect", attrs: { x: 98, y: 146, width: 26, height: 244, rx: 4, fill: "#1e293b", stroke: "#475569", "stroke-width": 1 } },
            { tag: "rect", attrs: { x: 676, y: 146, width: 26, height: 244, rx: 4, fill: "#1e293b", stroke: "#475569", "stroke-width": 1 } },
            { tag: "text", attrs: { x: 400, y: 205, "text-anchor": "middle", fill: "#94a3b8", "font-size": 9, "font-weight": 700 }, text: "AISLE" }
        ],
        zones: [
            {
                id: "Z1", name: "Orchestra Left", description: "Front-left tiered seating rows near the stage apron.",
                initialCrowd: 420, maxCapacity: 600, bottleneckBias: 0.95,
                shapeType: "rect", shapeAttrs: { x: 138, y: 146, width: 230, height: 106, rx: 10 },
                labelPos: { x: 253, y: 188 }
            },
            {
                id: "Z2", name: "Orchestra Right", description: "Front-right tiered seating rows near the stage apron.",
                initialCrowd: 485, maxCapacity: 600, bottleneckBias: 1.15,
                shapeType: "rect", shapeAttrs: { x: 432, y: 146, width: 230, height: 106, rx: 10 },
                labelPos: { x: 547, y: 188 }
            },
            {
                id: "Z3", name: "Mezzanine Left", description: "Rear-left raised seating block off the west side aisle.",
                initialCrowd: 290, maxCapacity: 500, bottleneckBias: 0.75,
                shapeType: "rect", shapeAttrs: { x: 138, y: 274, width: 230, height: 108, rx: 10 },
                labelPos: { x: 253, y: 318 }
            },
            {
                id: "Z4", name: "Mezzanine Right", description: "Rear-right raised seating block off the east side aisle.",
                initialCrowd: 390, maxCapacity: 500, bottleneckBias: 1.05,
                shapeType: "rect", shapeAttrs: { x: 432, y: 274, width: 230, height: 108, rx: 10 },
                labelPos: { x: 547, y: 318 }
            },
            {
                id: "Z5", name: "Central Cross-Aisle Hub", description: "Mid-hall intersection linking orchestra and mezzanine aisles.",
                initialCrowd: 225, maxCapacity: 260, bottleneckBias: 1.4,
                shapeType: "rect", shapeAttrs: { x: 332, y: 236, width: 136, height: 54, rx: 8 },
                labelPos: { x: 400, y: 255 }
            },
            {
                id: "Z6", name: "Grand Entrance Foyer", description: "Main lobby outside auditorium doors; high surge during intermission.",
                initialCrowd: 740, maxCapacity: 800, bottleneckBias: 1.45,
                shapeType: "rect", shapeAttrs: { x: 138, y: 398, width: 524, height: 62, rx: 10 },
                labelPos: { x: 400, y: 422 }
            }
        ],
        connections: [
            ["Z6", "Z3"], ["Z6", "Z4"], ["Z6", "Z5"],
            ["Z5", "Z1"], ["Z5", "Z2"],
            ["Z3", "Z1"], ["Z4", "Z2"]
        ],
        gates: [
            { label: "Main In", type: "entry", x: 400, y: 478 },
            { label: "W-Exit", type: "exit", x: 82, y: 428 },
            { label: "E-Exit", type: "exit", x: 718, y: 428 },
            { label: "EM-L", type: "emergency", x: 82, y: 170 },
            { label: "EM-R", type: "emergency", x: 718, y: 170 }
        ],
        facilityPositions: {
            food: { x: 138, y: 8 },
            entry: { x: 342, y: 474 },
            washrooms: { x: 660, y: 136 },
            medical: { x: 8, y: 254 },
            emergency: { x: 616, y: 420 },
            merchandise: { x: 282, y: 8 },
            parking: { x: 8, y: 390 },
            security: { x: 8, y: 8 }
        }
    },

    "exhibition-ground": {
        name: "Exhibition Ground",
        subtitle: "Convention Hall • Exhibition booth pavilions, cross-corridors & food court",
        architecture: [
            // Convention center shell
            { tag: "rect", attrs: { x: 32, y: 28, width: 736, height: 444, rx: 14, fill: "#0f172a", stroke: "#334155", "stroke-width": 2.5 } },
            // Wide Main Cross Corridors (N-S Boulevard & E-W Concourse)
            { tag: "rect", attrs: { x: 368, y: 44, width: 48, height: 412, fill: "#172554", stroke: "#1d4ed8", "stroke-width": 1, opacity: 0.6 } },
            { tag: "rect", attrs: { x: 48, y: 228, width: 704, height: 48, fill: "#172554", stroke: "#1d4ed8", "stroke-width": 1, opacity: 0.6 } },
            { tag: "text", attrs: { x: 210, y: 256, "text-anchor": "middle", fill: "#93c5fd", "font-size": 11, "font-weight": 700, "letter-spacing": 1 }, text: "MAIN EAST-WEST CORRIDOR" },
            { tag: "text", attrs: { x: 580, y: 256, "text-anchor": "middle", fill: "#93c5fd", "font-size": 11, "font-weight": 700, "letter-spacing": 1 }, text: "CONCOURSE WALKWAY" }
        ],
        zones: [
            {
                id: "Z1", name: "Tech Pavilion (Booths A1-A6)", description: "Hardware & consumer electronics exhibition booths.",
                initialCrowd: 1320, maxCapacity: 2000, bottleneckBias: 1.05,
                shapeType: "rect", shapeAttrs: { x: 52, y: 50, width: 298, height: 162, rx: 10 },
                labelPos: { x: 201, y: 120 }
            },
            {
                id: "Z2", name: "AI & Robotics Hall (B1-B4)", description: "Live autonomous robotics and AI showcase booths.",
                initialCrowd: 1680, maxCapacity: 1900, bottleneckBias: 1.45,
                shapeType: "rect", shapeAttrs: { x: 432, y: 50, width: 170, height: 162, rx: 10 },
                labelPos: { x: 517, y: 120 }
            },
            {
                id: "Z3", name: "Food Court & Lounge", description: "Indoor dining tables, coffee kiosks, and seating pods.",
                initialCrowd: 940, maxCapacity: 1200, bottleneckBias: 1.25,
                shapeType: "rect", shapeAttrs: { x: 618, y: 50, width: 130, height: 162, rx: 10 },
                labelPos: { x: 683, y: 120 }
            },
            {
                id: "Z4", name: "Startup Showcase (C1-C6)", description: "Early-stage exhibitor stalls along the southwest wing.",
                initialCrowd: 760, maxCapacity: 1800, bottleneckBias: 0.75,
                shapeType: "rect", shapeAttrs: { x: 52, y: 292, width: 210, height: 158, rx: 10 },
                labelPos: { x: 157, y: 360 }
            },
            {
                id: "Z5", name: "Keynote & Demo Arena", description: "Open-floor presentation stage for product launches.",
                initialCrowd: 1180, maxCapacity: 1500, bottleneckBias: 1.3,
                shapeType: "rect", shapeAttrs: { x: 278, y: 292, width: 182, height: 158, rx: 10 },
                labelPos: { x: 369, y: 360 }
            },
            {
                id: "Z6", name: "Registration & Entry Hall", description: "Badge pickup counters, QR turnstiles, and visitor lobby.",
                initialCrowd: 1290, maxCapacity: 1600, bottleneckBias: 1.2,
                shapeType: "rect", shapeAttrs: { x: 476, y: 292, width: 146, height: 158, rx: 10 },
                labelPos: { x: 549, y: 360 }
            },
            {
                id: "Z7", name: "East Exit & Shuttle Bay", description: "East concourse exit leading to shuttle buses and parking.",
                initialCrowd: 480, maxCapacity: 1400, bottleneckBias: 0.6,
                shapeType: "rect", shapeAttrs: { x: 638, y: 292, width: 110, height: 158, rx: 10 },
                labelPos: { x: 693, y: 360 }
            }
        ],
        connections: [
            ["Z6", "Z5"], ["Z6", "Z2"], ["Z6", "Z7"],
            ["Z5", "Z4"], ["Z5", "Z1"],
            ["Z1", "Z2"], ["Z2", "Z3"], ["Z3", "Z7"]
        ],
        gates: [
            { label: "Reg Entry", type: "entry", x: 549, y: 474 },
            { label: "VIP In", type: "entry", x: 392, y: 24 },
            { label: "West Out", type: "exit", x: 22, y: 252 },
            { label: "East Out", type: "exit", x: 778, y: 252 },
            { label: "EM-NW", type: "emergency", x: 68, y: 24 },
            { label: "EM-NE", type: "emergency", x: 732, y: 24 },
            { label: "EM-SW", type: "emergency", x: 157, y: 474 }
        ],
        facilityPositions: {
            food: { x: 622, y: 8 },
            entry: { x: 506, y: 442 },
            washrooms: { x: 646, y: 204 },
            medical: { x: -30, y: 330 },
            emergency: { x: 160, y: 442 },
            merchandise: { x: 120, y: 8 },
            parking: { x: 704, y: 447 },
            security: { x: 278, y: 8 }
        }
    }
};

const FACILITY_TYPES = [
    { id: "food", emoji: "🍔", label: "Food stalls", shortLabel: "Food", description: "Food and drink stalls serving visitors.", color: "#f59e0b", width: 132 },
    { id: "entry", emoji: "🚪", label: "Entry gates", shortLabel: "Entry", description: "Primary entry lanes for ticket checks and screening.", color: "#0ea5e9", width: 132 },
    { id: "washrooms", emoji: "🚻", label: "Washrooms", shortLabel: "Washrooms", description: "Public washrooms for venue guests.", color: "#8b5cf6", width: 130 },
    { id: "medical", emoji: "🏥", label: "Medical centres", shortLabel: "Medical", description: "First aid and medical assistance.", color: "#ef4444", width: 176 },
    { id: "emergency", emoji: "🚨", label: "Emergency exits", shortLabel: "Emergency", description: "Emergency egress points. Follow staff directions.", color: "#f97316", width: 176 },
    { id: "merchandise", emoji: "🛍️", label: "Merchandise", shortLabel: "Merch", description: "Official merchandise and event retail.", color: "#ec4899", width: 144 },
    { id: "parking", emoji: "🅿️", label: "Parking", shortLabel: "Parking", description: "Visitor parking and drop-off areas.", color: "#22c55e", width: 108 },
    { id: "security", emoji: "🛡️", label: "Security", shortLabel: "Security", description: "Security screening and guest assistance.", color: "#64748b", width: 120 }
];

// ==========================================================================
// 2. SIMULATOR STATE & DOM REFERENCES
// ==========================================================================

const SVG_NS = "http://www.w3.org/2000/svg";

const state = {
    currentVenueKey: "sports-stadium",
    zones: [],
    selectedZoneId: null,
    isRunning: false,
    tickCount: 0,
    timerId: null,
    activeFlows: [],
    history: {
        labels: [],
        totalCrowd: [],
        movementVolume: []
    }
};

const charts = {
    occupancy: null,
    movement: null,
    distribution: null,
    available: false
};

const dom = {
    datetime: document.getElementById("current-datetime"),
    totalCrowd: document.getElementById("total-crowd"),
    congestedZones: document.getElementById("congested-zones"),
    safeZones: document.getElementById("safe-zones"),
    predictedBottlenecks: document.getElementById("predicted-bottlenecks"),

    venueSelect: document.getElementById("venue-select"),
    venueSubtitle: document.getElementById("venue-subtitle"),
    startBtn: document.getElementById("sim-start-btn"),
    pauseBtn: document.getElementById("sim-pause-btn"),
    resetBtn: document.getElementById("sim-reset-btn"),
    simStatusBadge: document.getElementById("sim-status-badge"),

    mapStage: document.getElementById("stadium-map-container"),
    svg: document.getElementById("venue-svg"),
    facilityMarkerLayer: document.getElementById("facility-marker-layer"),
    facilityLegend: document.getElementById("facility-legend"),
    tooltip: document.getElementById("map-tooltip"),
    facilityPopup: document.getElementById("map-facility-popup"),
    facilityPopupClose: document.getElementById("facility-popup-close"),
    facilityPopupTitle: document.getElementById("facility-popup-title"),
    facilityPopupLocation: document.getElementById("facility-popup-location"),
    facilityPopupDescription: document.getElementById("facility-popup-description"),

    detailZoneId: document.getElementById("detail-zone-id"),
    detailDensityBadge: document.getElementById("detail-density-badge"),
    detailZoneName: document.getElementById("detail-zone-name"),
    detailZoneDesc: document.getElementById("detail-zone-desc"),
    detailCurrentCrowd: document.getElementById("detail-current-crowd"),
    detailMaxCapacity: document.getElementById("detail-max-capacity"),
    detailOccupancy: document.getElementById("detail-occupancy"),
    detailDensityText: document.getElementById("detail-density-text"),
    detailOccupancyBar: document.getElementById("detail-occupancy-bar"),
    detailConnections: document.getElementById("detail-connections"),

    analyticsContainer: document.getElementById("crowd-analytics-container"),
    analyticsFallback: document.getElementById("analytics-fallback"),
    analyticsSubtitle: document.getElementById("analytics-subtitle"),
    analyticsStatusBadge: document.getElementById("analytics-status-badge"),
    occupancyCanvas: document.getElementById("occupancy-bar-chart"),
    movementCanvas: document.getElementById("movement-line-chart"),
    distributionCanvas: document.getElementById("density-dist-chart")
};

// ==========================================================================
// 3. HELPER FUNCTIONS (DENSITY MATH, SVG CREATION, CLOCK)
// ==========================================================================

function createSvgElement(tag, attrs = {}, textContent = "") {
    const el = document.createElementNS(SVG_NS, tag);
    Object.entries(attrs).forEach(([key, value]) => {
        el.setAttribute(key, value);
    });
    if (textContent) {
        el.textContent = textContent;
    }
    return el;
}

/**
 * Calculates occupancy % = (Current Crowd / Maximum Capacity) * 100
 * and maps it to one of the four density color levels.
 */
function getDensityInfo(currentCrowd, maxCapacity) {
    const occupancy = maxCapacity > 0 ? (currentCrowd / maxCapacity) * 100 : 0;

    if (occupancy >= 90) {
        return {
            occupancy,
            level: "critical",
            label: "Critical",
            fillColor: "rgba(239, 68, 68, 0.38)",
            strokeColor: "#ef4444",
            barColor: "#ef4444",
            pillClass: "pill pill-critical"
        };
    }
    if (occupancy >= 75) {
        return {
            occupancy,
            level: "high",
            label: "High",
            fillColor: "rgba(249, 115, 22, 0.35)",
            strokeColor: "#f97316",
            barColor: "#f97316",
            pillClass: "pill pill-high"
        };
    }
    if (occupancy >= 50) {
        return {
            occupancy,
            level: "medium",
            label: "Medium",
            fillColor: "rgba(234, 179, 8, 0.32)",
            strokeColor: "#eab308",
            barColor: "#eab308",
            pillClass: "pill pill-medium"
        };
    }
    return {
        occupancy,
        level: "low",
        label: "Low",
        fillColor: "rgba(34, 197, 94, 0.28)",
        strokeColor: "#22c55e",
        barColor: "#22c55e",
        pillClass: "pill pill-low"
    };
}

function updateClock() {
    if (!dom.datetime) return;
    const now = new Date();
    dom.datetime.textContent = now.toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });
}

// ==========================================================================
// 4. SVG VENUE RENDERER (REUSABLE ACROSS ALL 5 VENUE TYPES)
// ==========================================================================

function loadVenue(venueKey) {
    pauseSimulation();
    state.currentVenueKey = venueKey;
    state.tickCount = 0;
    state.activeFlows = [];

    const preset = VENUE_PRESETS[venueKey];
    state.zones = preset.zones.map((z) => ({
        ...z,
        currentCrowd: z.initialCrowd,
        previousCrowd: z.initialCrowd
    }));

    // Select the first zone by default so details panel is populated immediately
    state.selectedZoneId = state.zones[0]?.id || null;
    dom.venueSubtitle.textContent = preset.subtitle;

    resetHistory();
    hideTooltip();
    hideFacilityPopup();
    renderSvgVenue(preset);
    updateAllViews();
    updateControlButtons();
}

function renderSvgVenue(preset) {
    dom.svg.innerHTML = "";

    // Reusable SVG <defs> for directional movement arrowheads
    const defs = createSvgElement("defs");
    defs.appendChild(buildArrowMarker("flow-arrow", "#38bdf8"));
    defs.appendChild(buildArrowMarker("flow-arrow-active", "#facc15"));
    dom.svg.appendChild(defs);

    // 1. Venue-specific architecture (walls, stage/pitch, aisles)
    const archGroup = createSvgElement("g", { class: "layer-architecture" });
    preset.architecture.forEach((item) => {
        archGroup.appendChild(createSvgElement(item.tag, item.attrs, item.text || ""));
    });
    dom.svg.appendChild(archGroup);

    // 2. Interactive crowd zones
    const zonesGroup = createSvgElement("g", { class: "layer-zones" });
    state.zones.forEach((zone) => {
        const g = createSvgElement("g", {
            class: "venue-zone",
            "data-zone-id": zone.id,
            tabindex: "0",
            role: "button",
            "aria-label": `${zone.id} ${zone.name}`
        });

        const shape = createSvgElement(zone.shapeType, {
            ...zone.shapeAttrs,
            class: "zone-shape"
        });
        g.appendChild(shape);

        // Zone ID, Name, and Occupancy % labels
        g.appendChild(createSvgElement("text", {
            x: zone.labelPos.x,
            y: zone.labelPos.y - 4,
            class: "zone-label-id"
        }, zone.id));

        g.appendChild(createSvgElement("text", {
            x: zone.labelPos.x,
            y: zone.labelPos.y + 11,
            class: "zone-label-name"
        }, zone.name));

        g.appendChild(createSvgElement("text", {
            x: zone.labelPos.x,
            y: zone.labelPos.y + 26,
            class: "zone-label-pct"
        }, "0%"));

        // Click + Keyboard + Hover interactions
        g.addEventListener("click", () => selectZone(zone.id));
        g.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                selectZone(zone.id);
            }
        });
        g.addEventListener("mouseenter", (e) => showTooltip(e, zone.id));
        g.addEventListener("mousemove", (e) => moveTooltip(e));
        g.addEventListener("mouseleave", hideTooltip);

        zonesGroup.appendChild(g);
    });
    dom.svg.appendChild(zonesGroup);

    // 3. Optional overlay architecture (e.g., center stage above arena floor)
    if (preset.overlayArchitecture) {
        const overlayGroup = createSvgElement("g", { class: "layer-overlay" });
        preset.overlayArchitecture.forEach((item) => {
            overlayGroup.appendChild(createSvgElement(item.tag, item.attrs, item.text || ""));
        });
        dom.svg.appendChild(overlayGroup);
    }

    // 4. Movement paths between connected zones
    const flowsGroup = createSvgElement("g", { class: "layer-flows" });
    preset.connections.forEach(([fromId, toId]) => {
        const fromZone = state.zones.find((z) => z.id === fromId);
        const toZone = state.zones.find((z) => z.id === toId);
        if (!fromZone || !toZone) return;

        const pathKey = `${fromId}-${toId}`;
        const flowG = createSvgElement("g", { "data-flow-key": pathKey });

        const line = createSvgElement("line", {
            x1: fromZone.labelPos.x,
            y1: fromZone.labelPos.y,
            x2: toZone.labelPos.x,
            y2: toZone.labelPos.y,
            class: "flow-path",
            "marker-end": "url(#flow-arrow)"
        });
        flowG.appendChild(line);

        // Midpoint flow badge (hidden unless active movement occurs)
        const midX = (fromZone.labelPos.x + toZone.labelPos.x) / 2;
        const midY = (fromZone.labelPos.y + toZone.labelPos.y) / 2;

        const badgeBg = createSvgElement("rect", {
            x: midX - 18,
            y: midY - 9,
            width: 36,
            height: 16,
            rx: 6,
            class: "flow-badge-bg",
            visibility: "hidden"
        });
        const badgeText = createSvgElement("text", {
            x: midX,
            y: midY + 2.5,
            class: "flow-badge-text",
            visibility: "hidden"
        }, "");

        flowG.appendChild(badgeBg);
        flowG.appendChild(badgeText);
        flowsGroup.appendChild(flowG);
    });
    dom.svg.appendChild(flowsGroup);

    // 5. Entry, Exit & Emergency Gate Markers
    const gatesGroup = createSvgElement("g", { class: "layer-gates" });
    preset.gates.forEach((gate) => {
        const colorMap = {
            entry: "#0284c7",
            exit: "#0d9488",
            emergency: "#dc2626"
        };
        const fill = colorMap[gate.type] || "#475569";

        const g = createSvgElement("g", { transform: `translate(${gate.x}, ${gate.y})` });
        g.appendChild(createSvgElement("rect", {
            x: -26,
            y: -10,
            width: 52,
            height: 20,
            rx: 5,
            fill,
            stroke: "#f8fafc",
            "stroke-width": 1
        }));
        g.appendChild(createSvgElement("text", {
            x: 0,
            y: 3.5,
            "text-anchor": "middle",
            fill: "#ffffff",
            "font-size": 9.5,
            "font-weight": 700
        }, gate.label));
        gatesGroup.appendChild(g);
    });
    dom.svg.appendChild(gatesGroup);

    renderFacilityMarkers(preset);
}

function renderFacilityLegend() {
    dom.facilityLegend.replaceChildren();
    FACILITY_TYPES.forEach((facility) => {
        const item = document.createElement("span");
        item.className = "facility-key-item";
        item.setAttribute("role", "listitem");

        const icon = document.createElement("span");
        icon.className = "facility-key-icon";
        icon.style.setProperty("--facility-color", facility.color);
        icon.setAttribute("aria-hidden", "true");
        icon.textContent = facility.emoji;

        const label = document.createElement("span");
        label.textContent = facility.label;

        item.append(icon, label);
        dom.facilityLegend.appendChild(item);
    });
}

function getNearestFacilityZone(position, facility) {
    const markerCenter = {
        x: position.x + facility.width / 2,
        y: position.y + 19
    };

    return state.zones.reduce((nearest, zone) => {
        const distance = Math.hypot(
            zone.labelPos.x - markerCenter.x,
            zone.labelPos.y - markerCenter.y
        );
        return !nearest || distance < nearest.distance
            ? { zone, distance }
            : nearest;
    }, null)?.zone || null;
}

function renderFacilityMarkers(preset) {
    dom.facilityMarkerLayer.replaceChildren();
    FACILITY_TYPES.forEach((facility) => {
        const position = preset.facilityPositions[facility.id];
        const zone = getNearestFacilityZone(position, facility);
        const marker = document.createElement("button");
        marker.type = "button";
        marker.className = "facility-marker";
        marker.dataset.facilityId = facility.id;
        marker.style.left = `${((position.x + facility.width / 2) / 800) * 100}%`;
        marker.style.top = `${((position.y + 19) / 500) * 100}%`;
        marker.style.setProperty("--facility-color", facility.color);

        const location = zone ? `Near ${zone.id} · ${zone.name}` : "Venue perimeter";
        marker.setAttribute("aria-label", `${facility.emoji} ${facility.label}. ${location}. ${facility.description}`);
        marker.title = `${facility.label} — ${location}. ${facility.description}`;

        const icon = document.createElement("span");
        icon.className = "facility-marker-emoji";
        icon.setAttribute("aria-hidden", "true");
        icon.textContent = facility.emoji;

        const label = document.createElement("span");
        label.className = "facility-marker-label";
        label.textContent = facility.shortLabel;

        marker.append(icon, label);
        marker.addEventListener("mouseenter", (event) => showFacilityTooltip(event, facility, zone, marker));
        marker.addEventListener("mousemove", moveTooltip);
        marker.addEventListener("mouseleave", hideTooltip);
        marker.addEventListener("focus", (event) => showFacilityTooltip(event, facility, zone, marker));
        marker.addEventListener("blur", hideTooltip);
        marker.addEventListener("click", () => {
            hideTooltip();
            showFacilityPopup(facility, marker, zone);
        });
        dom.facilityMarkerLayer.appendChild(marker);
    });
}

function showFacilityTooltip(event, facility, zone, marker) {
    const title = document.createElement("strong");
    title.textContent = `${facility.emoji} ${facility.label}`;
    const location = document.createElement("div");
    location.textContent = zone ? `Near ${zone.id} · ${zone.name}` : "Venue perimeter";
    const description = document.createElement("div");
    description.textContent = facility.description;
    dom.tooltip.replaceChildren(title, location, description);
    dom.tooltip.hidden = false;

    const markerRect = marker.getBoundingClientRect();
    const pointerPosition = event.type === "focus"
        ? {
            clientX: markerRect.left + markerRect.width / 2,
            clientY: markerRect.top + markerRect.height / 2
        }
        : event;
    moveTooltip(pointerPosition);
}

function showFacilityPopup(facility, marker, zone) {
    dom.facilityPopupTitle.textContent = `${facility.emoji} ${facility.label}`;
    dom.facilityPopupLocation.textContent = zone
        ? `Near ${zone.id} · ${zone.name}`
        : "Venue perimeter";
    dom.facilityPopupDescription.textContent = facility.description;
    dom.facilityPopup.hidden = false;

    const markerRect = marker.getBoundingClientRect();
    const stageRect = dom.mapStage.getBoundingClientRect();
    const popupWidth = dom.facilityPopup.offsetWidth;
    const popupHeight = dom.facilityPopup.offsetHeight;
    const markerCenterX = markerRect.left - stageRect.left + markerRect.width / 2;
    const halfPopup = popupWidth / 2;
    const left = Math.max(halfPopup + 8, Math.min(stageRect.width - halfPopup - 8, markerCenterX));
    let placeBelow = markerRect.top - stageRect.top < popupHeight + 16;
    let top = placeBelow
        ? markerRect.bottom - stageRect.top + 8
        : markerRect.top - stageRect.top - 8;

    if (placeBelow && top + popupHeight > stageRect.height - 8) {
        placeBelow = false;
        top = markerRect.top - stageRect.top - 8;
    }

    dom.facilityPopup.classList.toggle("is-below", placeBelow);
    dom.facilityPopup.style.left = `${left}px`;
    dom.facilityPopup.style.top = `${top}px`;
}

function hideFacilityPopup() {
    dom.facilityPopup.hidden = true;
    dom.facilityPopup.classList.remove("is-below");
}

function buildArrowMarker(id, color) {
    const marker = createSvgElement("marker", {
        id,
        viewBox: "0 0 10 10",
        refX: 8,
        refY: 5,
        markerWidth: 6,
        markerHeight: 6,
        orient: "auto-start-reverse"
    });
    marker.appendChild(createSvgElement("path", {
        d: "M 0 1 L 10 5 L 0 9 z",
        fill: color
    }));
    return marker;
}

// ==========================================================================
// 5. INTERACTIONS (SELECT ZONE, TOOLTIP) & UI UPDATES
// ==========================================================================

function selectZone(zoneId) {
    state.selectedZoneId = zoneId;
    updateZoneVisuals();
    updateDetailsPanel();
}

function showTooltip(event, zoneId) {
    const zone = state.zones.find((z) => z.id === zoneId);
    if (!zone) return;

    const density = getDensityInfo(zone.currentCrowd, zone.maxCapacity);
    dom.tooltip.innerHTML = `
        <strong>${zone.id}: ${zone.name}</strong>
        <div>Crowd: ${zone.currentCrowd.toLocaleString()} / ${zone.maxCapacity.toLocaleString()}</div>
        <div>Occupancy: ${density.occupancy.toFixed(1)}% (${density.label})</div>
    `;
    dom.tooltip.hidden = false;
    moveTooltip(event);
}

function moveTooltip(event) {
    if (dom.tooltip.hidden) return;
    const stageRect = dom.mapStage.getBoundingClientRect();
    const offsetX = event.clientX - stageRect.left + 14;
    const offsetY = event.clientY - stageRect.top + 14;

    const maxLeft = Math.max(8, stageRect.width - 195);
    const maxTop = Math.max(8, stageRect.height - 90);

    dom.tooltip.style.left = `${Math.min(offsetX, maxLeft)}px`;
    dom.tooltip.style.top = `${Math.min(offsetY, maxTop)}px`;
}

function hideTooltip() {
    dom.tooltip.hidden = true;
}

function updateAllViews() {
    updateZoneVisuals();
    updateFlowVisuals();
    updateDetailsPanel();
    updateOverviewCards();
    updateCharts();
}

function updateZoneVisuals() {
    state.zones.forEach((zone) => {
        const zoneGroup = dom.svg.querySelector(`.venue-zone[data-zone-id="${zone.id}"]`);
        if (!zoneGroup) return;

        const density = getDensityInfo(zone.currentCrowd, zone.maxCapacity);
        const shape = zoneGroup.querySelector(".zone-shape");
        const pctLabel = zoneGroup.querySelector(".zone-label-pct");

        shape.setAttribute("fill", density.fillColor);
        shape.setAttribute("stroke", density.strokeColor);
        pctLabel.textContent = `${Math.round(density.occupancy)}%`;

        zoneGroup.classList.toggle("is-selected", zone.id === state.selectedZoneId);
    });
}

function updateFlowVisuals() {
    const flowElements = dom.svg.querySelectorAll("[data-flow-key]");
    flowElements.forEach((flowG) => {
        const key = flowG.getAttribute("data-flow-key");
        const active = state.activeFlows.find((f) => f.key === key);
        const line = flowG.querySelector(".flow-path");
        const badgeBg = flowG.querySelector(".flow-badge-bg");
        const badgeText = flowG.querySelector(".flow-badge-text");

        if (active && state.isRunning) {
            line.classList.add("flow-active");
            line.setAttribute("marker-end", "url(#flow-arrow-active)");
            badgeBg.setAttribute("visibility", "visible");
            badgeText.setAttribute("visibility", "visible");
            badgeText.textContent = `+${active.count}`;
        } else {
            line.classList.remove("flow-active");
            line.setAttribute("marker-end", "url(#flow-arrow)");
            badgeBg.setAttribute("visibility", "hidden");
            badgeText.setAttribute("visibility", "hidden");
        }
    });
}

function updateDetailsPanel() {
    const zone = state.zones.find((z) => z.id === state.selectedZoneId);
    if (!zone) return;

    const density = getDensityInfo(zone.currentCrowd, zone.maxCapacity);
    const preset = VENUE_PRESETS[state.currentVenueKey];

    dom.detailZoneId.textContent = `${preset.name.toUpperCase()} • ${zone.id}`;
    dom.detailZoneName.textContent = zone.name;
    dom.detailZoneDesc.textContent = zone.description;

    dom.detailDensityBadge.textContent = density.label;
    dom.detailDensityBadge.className = density.pillClass;

    dom.detailCurrentCrowd.textContent = zone.currentCrowd.toLocaleString();
    dom.detailMaxCapacity.textContent = zone.maxCapacity.toLocaleString();
    dom.detailOccupancy.textContent = `${density.occupancy.toFixed(1)}%`;
    dom.detailDensityText.textContent = density.label;

    const barWidth = Math.min(100, Math.max(0, density.occupancy));
    dom.detailOccupancyBar.style.width = `${barWidth}%`;
    dom.detailOccupancyBar.style.backgroundColor = density.barColor;

    // Show connected zones & recent movement delta
    const connectedIds = preset.connections
        .filter(([fromId, toId]) => fromId === zone.id || toId === zone.id)
        .map(([fromId, toId]) => (fromId === zone.id ? toId : fromId));

    const connectedNames = connectedIds
        .map((id) => {
            const match = state.zones.find((z) => z.id === id);
            return match ? `${match.id} (${match.name})` : id;
        })
        .join(", ");

    const delta = zone.currentCrowd - zone.previousCrowd;
    const trendText = delta === 0 ? "Stable" : delta > 0 ? `+${delta} inflow` : `${delta} outflow`;
    dom.detailConnections.textContent = connectedNames
        ? `${connectedNames} • Trend: ${trendText}`
        : `Trend: ${trendText}`;
}

function updateOverviewCards() {
    let total = 0;
    let congested = 0;
    let safe = 0;
    let predicted = 0;

    state.zones.forEach((zone) => {
        total += zone.currentCrowd;
        const { occupancy } = getDensityInfo(zone.currentCrowd, zone.maxCapacity);
        if (occupancy >= 75) {
            congested += 1;
        } else {
            safe += 1;
        }
        // Zones between 65% and 89% or rising fast count toward short-term bottleneck watch
        if (occupancy >= 65 && occupancy < 90) {
            predicted += 1;
        }
    });

    dom.totalCrowd.textContent = total.toLocaleString();
    dom.congestedZones.textContent = String(congested).padStart(2, "0");
    dom.safeZones.textContent = String(safe).padStart(2, "0");
    dom.predictedBottlenecks.textContent = String(predicted).padStart(2, "0");
}

// ==========================================================================
// 6. CROWD SIMULATION LOOP (START / PAUSE / RESET)
// ==========================================================================

function stepSimulation() {
    const preset = VENUE_PRESETS[state.currentVenueKey];
    state.tickCount += 1;
    state.activeFlows = [];

    // Save previous counts to calculate trend delta
    state.zones.forEach((zone) => {
        zone.previousCrowd = zone.currentCrowd;
    });

    // 1. Simulate crowd movement along connected corridors
    preset.connections.forEach(([fromId, toId]) => {
        const fromZone = state.zones.find((z) => z.id === fromId);
        const toZone = state.zones.find((z) => z.id === toId);
        if (!fromZone || !toZone) return;

        // Move a small realistic batch of people (1% to 3.5% of source crowd)
        const rate = 0.01 + Math.random() * 0.025;
        let transfer = Math.round(fromZone.currentCrowd * rate);

        // Keep counts within valid bounds [0, maxCapacity]
        const availableSpace = toZone.maxCapacity - toZone.currentCrowd;
        transfer = Math.min(transfer, fromZone.currentCrowd, availableSpace);

        if (transfer > 0) {
            fromZone.currentCrowd -= transfer;
            toZone.currentCrowd += transfer;
            state.activeFlows.push({
                key: `${fromId}-${toId}`,
                count: transfer
            });
        }
    });

    // 2. Simulate gradual venue arrivals/departures so some zones heat up over time
    state.zones.forEach((zone) => {
        const baseStep = Math.round(zone.maxCapacity * (0.008 + Math.random() * 0.015));
        const surgeChance = zone.bottleneckBias > 1 ? 0.72 : 0.45;
        const delta = Math.random() < surgeChance ? baseStep : -Math.round(baseStep * 0.7);
        zone.currentCrowd = Math.max(0, Math.min(zone.maxCapacity, zone.currentCrowd + delta));
    });

    recordHistoryPoint();
    updateAllViews();
    updateControlButtons();
}

function startSimulation() {
    if (state.isRunning) return;
    state.isRunning = true;
    stepSimulation();
    state.timerId = setInterval(stepSimulation, 1400);
    updateControlButtons();
    updateAnalyticsStatus();
}

function pauseSimulation() {
    if (state.timerId) {
        clearInterval(state.timerId);
        state.timerId = null;
    }
    state.isRunning = false;
    updateFlowVisuals();
    updateControlButtons();
    updateCharts();
}

function resetSimulation() {
    pauseSimulation();
    state.tickCount = 0;
    state.activeFlows = [];
    state.zones.forEach((zone) => {
        zone.currentCrowd = zone.initialCrowd;
        zone.previousCrowd = zone.initialCrowd;
    });
    resetHistory();
    updateAllViews();
    updateControlButtons();
}

function updateControlButtons() {
    dom.startBtn.disabled = state.isRunning;
    dom.pauseBtn.disabled = !state.isRunning;

    if (state.isRunning) {
        dom.simStatusBadge.textContent = `Running • Step ${state.tickCount}`;
        dom.simStatusBadge.className = "badge badge-success";
    } else {
        dom.simStatusBadge.textContent = state.tickCount > 0 ? `Paused (Step ${state.tickCount})` : "Ready (Paused)";
        dom.simStatusBadge.className = "badge badge-neutral";
    }
}

// ==========================================================================
// 7. CROWD DENSITY ANALYTICS (CHART.JS)
// ==========================================================================

const MAX_HISTORY_POINTS = 12;

function getTotalCrowd() {
    return state.zones.reduce((sum, z) => sum + z.currentCrowd, 0);
}

function getMovementVolume() {
    return state.activeFlows.reduce((sum, f) => sum + f.count, 0);
}

function resetHistory() {
    state.history = {
        labels: ["Start"],
        totalCrowd: [getTotalCrowd()],
        movementVolume: [0]
    };
}

function recordHistoryPoint() {
    state.history.labels.push(`Step ${state.tickCount}`);
    state.history.totalCrowd.push(getTotalCrowd());
    state.history.movementVolume.push(getMovementVolume());

    if (state.history.labels.length > MAX_HISTORY_POINTS) {
        state.history.labels.shift();
        state.history.totalCrowd.shift();
        state.history.movementVolume.shift();
    }
}

function initCharts() {
    if (typeof window.Chart === "undefined") {
        charts.available = false;
        if (dom.analyticsFallback) dom.analyticsFallback.hidden = false;
        if (dom.analyticsContainer) dom.analyticsContainer.hidden = true;
        if (dom.analyticsStatusBadge) {
            dom.analyticsStatusBadge.textContent = "Chart.js Offline";
            dom.analyticsStatusBadge.className = "badge badge-warning";
        }
        return;
    }

    // Prevent duplicate instances if initCharts is ever called again
    [charts.occupancy, charts.movement, charts.distribution].forEach((instance) => {
        if (instance && typeof instance.destroy === "function") {
            instance.destroy();
        }
    });

    const gridColor = "rgba(148, 163, 184, 0.14)";
    const tickColor = "#94a3b8";
    const tooltipTheme = {
        backgroundColor: "#0b1120",
        titleColor: "#38bdf8",
        bodyColor: "#f1f5f9",
        borderColor: "#334155",
        borderWidth: 1
    };

    try {
        // 1. Zone-Wise Occupancy Bar Chart
        charts.occupancy = new window.Chart(dom.occupancyCanvas.getContext("2d"), {
            type: "bar",
            data: {
                labels: [],
                datasets: [{
                    label: "Occupancy %",
                    data: [],
                    backgroundColor: [],
                    borderColor: [],
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        ...tooltipTheme,
                        callbacks: {
                            title: (items) => {
                                const idx = items[0]?.dataIndex ?? 0;
                                const zone = state.zones[idx];
                                return zone ? `${zone.id}: ${zone.name}` : "";
                            },
                            label: (item) => {
                                const zone = state.zones[item.dataIndex];
                                return zone
                                    ? `Occupancy: ${item.formattedValue}% (${zone.currentCrowd.toLocaleString()} / ${zone.maxCapacity.toLocaleString()})`
                                    : `${item.formattedValue}%`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: tickColor },
                        grid: { display: false }
                    },
                    y: {
                        min: 0,
                        max: 100,
                        ticks: {
                            color: tickColor,
                            callback: (val) => `${val}%`
                        },
                        grid: { color: gridColor }
                    }
                }
            }
        });

        // 2. Crowd Movement Over Time Line Chart
        charts.movement = new window.Chart(dom.movementCanvas.getContext("2d"), {
            type: "line",
            data: {
                labels: [],
                datasets: [
                    {
                        label: "Total Crowd",
                        data: [],
                        borderColor: "#38bdf8",
                        backgroundColor: "rgba(56, 189, 248, 0.16)",
                        fill: true,
                        tension: 0.3,
                        pointRadius: 3,
                        yAxisID: "y"
                    },
                    {
                        label: "Zone Transfers",
                        data: [],
                        borderColor: "#facc15",
                        backgroundColor: "rgba(250, 204, 21, 0.15)",
                        fill: false,
                        tension: 0.3,
                        pointRadius: 3,
                        yAxisID: "y1"
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: "index", intersect: false },
                plugins: {
                    legend: {
                        labels: { color: "#cbd5e1", boxWidth: 12, font: { size: 11 } }
                    },
                    tooltip: tooltipTheme
                },
                scales: {
                    x: {
                        ticks: { color: tickColor, maxRotation: 0, autoSkip: true },
                        grid: { display: false }
                    },
                    y: {
                        type: "linear",
                        position: "left",
                        ticks: { color: "#38bdf8" },
                        grid: { color: gridColor }
                    },
                    y1: {
                        type: "linear",
                        position: "right",
                        min: 0,
                        ticks: { color: "#facc15" },
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });

        // 3. Crowd Density Distribution Chart (Low, Medium, High, Critical)
        charts.distribution = new window.Chart(dom.distributionCanvas.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: ["Low", "Medium", "High", "Critical"],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: ["#22c55e", "#eab308", "#f97316", "#ef4444"],
                    borderColor: "#0f172a",
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "62%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { color: "#cbd5e1", boxWidth: 12, padding: 12, font: { size: 11 } }
                    },
                    tooltip: {
                        ...tooltipTheme,
                        callbacks: {
                            label: (item) => ` ${item.label}: ${item.raw} zone(s)`
                        }
                    }
                }
            }
        });

        charts.available = true;
        if (dom.analyticsFallback) dom.analyticsFallback.hidden = true;
        if (dom.analyticsContainer) dom.analyticsContainer.hidden = false;
    } catch (err) {
        console.warn("Chart.js initialization failed; continuing simulator without charts:", err);
        charts.available = false;
        if (dom.analyticsFallback) dom.analyticsFallback.hidden = false;
        if (dom.analyticsContainer) dom.analyticsContainer.hidden = true;
    }
}

function updateAnalyticsStatus() {
    const preset = VENUE_PRESETS[state.currentVenueKey];
    if (dom.analyticsSubtitle && preset) {
        dom.analyticsSubtitle.textContent = `${preset.name} • Live simulated zone metrics`;
    }
    if (!dom.analyticsStatusBadge) return;

    if (!charts.available) {
        dom.analyticsStatusBadge.textContent = "Chart.js Offline";
        dom.analyticsStatusBadge.className = "badge badge-warning";
        return;
    }

    if (state.isRunning) {
        dom.analyticsStatusBadge.textContent = `Live • Step ${state.tickCount}`;
        dom.analyticsStatusBadge.className = "badge badge-success";
    } else {
        dom.analyticsStatusBadge.textContent = state.tickCount > 0
            ? `Paused • Step ${state.tickCount}`
            : "Synced • Ready";
        dom.analyticsStatusBadge.className = "badge badge-info";
    }
}

function updateCharts() {
    updateAnalyticsStatus();
    if (!charts.available) return;

    try {
        // 1. Update Zone-Wise Occupancy Bar Chart
        const labels = [];
        const occupancyData = [];
        const barColors = [];
        const borderColors = [];
        const distCounts = { low: 0, medium: 0, high: 0, critical: 0 };

        state.zones.forEach((zone) => {
            const density = getDensityInfo(zone.currentCrowd, zone.maxCapacity);
            labels.push(zone.id);
            occupancyData.push(Number(density.occupancy.toFixed(1)));
            barColors.push(density.fillColor);
            borderColors.push(density.strokeColor);
            distCounts[density.level] += 1;
        });

        charts.occupancy.data.labels = labels;
        charts.occupancy.data.datasets[0].data = occupancyData;
        charts.occupancy.data.datasets[0].backgroundColor = barColors;
        charts.occupancy.data.datasets[0].borderColor = borderColors;
        charts.occupancy.update("none");

        // 2. Update Crowd Movement Over Time Line Chart
        charts.movement.data.labels = [...state.history.labels];
        charts.movement.data.datasets[0].data = [...state.history.totalCrowd];
        charts.movement.data.datasets[1].data = [...state.history.movementVolume];
        charts.movement.update("none");

        // 3. Update Crowd Density Distribution Doughnut Chart
        charts.distribution.data.datasets[0].data = [
            distCounts.low,
            distCounts.medium,
            distCounts.high,
            distCounts.critical
        ];
        charts.distribution.update("none");
    } catch (err) {
        console.warn("Chart update error:", err);
    }
}

// ==========================================================================
// 8. EVENT LISTENERS & INITIALIZATION
// ==========================================================================

function initSimulator() {
    updateClock();
    setInterval(updateClock, 1000);

    initCharts();

    dom.venueSelect.addEventListener("change", (e) => {
        loadVenue(e.target.value);
    });

    dom.startBtn.addEventListener("click", startSimulation);
    dom.pauseBtn.addEventListener("click", pauseSimulation);
    dom.resetBtn.addEventListener("click", resetSimulation);
    dom.facilityPopupClose.addEventListener("click", hideFacilityPopup);
    window.addEventListener("resize", () => {
        hideTooltip();
        hideFacilityPopup();
    });

    renderFacilityLegend();
    loadVenue(state.currentVenueKey);
}

initSimulator();
