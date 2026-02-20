# Web3DP: 3D Printing Quote & Auto-Print Web App

## 1. Project Goal
Build a web application that allows users to upload `.stl` files, instantly view their 3D model, select filament/quantity, receive an instant quote, and submit an order. Once paid and approved by an admin, the system automatically slices the file and sends it to a Bambu Lab printer.

## 2. Architecture Overview

### Frontend (User & Admin)
*   **Framework:** React (Vite) + TypeScript
*   **Styling:** Tailwind CSS
*   **3D Visualization:** `three.js`, `@react-three/fiber`, `@react-three/drei`
    *   **Features:**
        *   Instant local loading of `.stl` files (drag-and-drop).
        *   Interactive 3D preview (rotate, zoom).
        *   Dynamic material color updates (e.g., selecting "Red PLA" changes the model color).
*   **State Management:** React Context / Zustand (if needed).
*   **API Client:** Axios / Fetch.

### Backend (API & Worker)
*   **Framework:** Python (FastAPI)
*   **Database:** SQLite (Lightweight, single-file, easy to back up).
*   **Core Services:**
    *   **File Analysis:** `numpy-stl` to calculate volume ($cm^3$) and bounding box.
    *   **Quoting Engine:** Calculates price based on material density, weight, machine time, and markup.
    *   **Slicing Engine:** Wrapper for **Bambu Studio CLI** (Linux AppImage).
    *   **Printer Control:**
        *   **MQTT:** Sends commands (Start Print, Pause, Stop) and monitors status.
        *   **FTPS:** Uploads `.3mf` / `.gcode` files to the printer.

## 3. Detailed Features & Workflow

### User Flow
1.  **Landing Page:**
    *   Drag-and-drop zone for `.stl` files.
    *   **Instant 3D Preview:** The uploaded file is rendered immediately in the browser using Three.js.
2.  **Configuration:**
    *   **Material Selection:** User selects Filament Type (PLA, PETG, ABS) and Color.
    *   **Visual Feedback:** The 3D model updates to reflect the selected color.
    *   **Quantity:** User inputs the number of parts needed.
3.  **Quoting:**
    *   Backend analyzes the STL geometry.
    *   Calculates: `Weight (g) = Volume (cm³) * Density (g/cm³)`.
    *   Price Formula: `(Weight * MaterialCost/g) + (Est. Print Time * MachineRate/hr) + StartupFee`.
    *   Displays instant price quote.
4.  **Checkout:**
    *   User enters shipping/payment details.
    *   Standard payment integration (Stripe/PayPal placeholder).
    *   Job status set to `PAID`.

### Admin Workflow
1.  **Dashboard:**
    *   View list of active jobs (Paid, Printing, Completed).
    *   See file details, user info, and estimated print time.
2.  **Approval & Slicing:**
    *   Admin clicks **"Approve & Print"**.
    *   **Auto-Slicing:** The server invokes Bambu Studio CLI to convert `.stl` -> `.3mf` using a standard profile.
    *   *Fallback:* If auto-slicing fails, Admin can manually slice and upload the `.gcode.3mf`.
3.  **Printing:**
    *   Server connects to the specific Bambu Lab printer (via IP/Access Code).
    *   Uploads the file via FTPS.
    *   Sends MQTT command to start the print.
    *   Updates Job Status to `PRINTING`.

## 4. Technical Requirements

### Server Environment
*   **OS:** Linux (Ubuntu Recommended) or macOS.
*   **Dependencies:**
    *   Python 3.10+
    *   **Bambu Studio AppImage:** Required for CLI slicing.
    *   `xvfb`: Virtual framebuffer (needed to run Bambu Studio headless on a server).

### Database Schema (SQLite)

#### `jobs`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | Primary Key |
| `status` | String | PENDING, PAID, SLICING, PRINTING, DONE |
| `filename` | String | Original STL filename |
| `filepath` | String | Path to stored STL |
| `material` | String | Selected material (e.g., "PLA_BASIC_RED") |
| `volume_cm3` | Float | Calculated volume |
| `price` | Float | Final quote price |
| `customer_email` | String | User contact |
| `created_at` | DateTime | Timestamp |

#### `materials`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | Primary Key |
| `name` | String | Display Name (e.g., "Bambu PLA Basic Red") |
| `type` | String | PLA, PETG, ABS, etc. |
| `density` | Float | g/cm³ (e.g., 1.24 for PLA) |
| `cost_per_g` | Float | Cost per gram (for pricing) |
| `hex_color` | String | Hex code for 3D viewer (e.g., #FF0000) |
| `bambu_filament_id` | String | ID used in Bambu Studio CLI |

#### `printers`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | Primary Key |
| `name` | String | Friendly Name (e.g., "P1S-01") |
| `ip_address` | String | Local IP |
| `access_code` | String | Access Code (from printer screen) |
| `serial_number` | String | Printer Serial |
| `status` | String | IDLE, PRINTING, OFFLINE |

## 5. Implementation Roadmap

1.  **Project Setup:** Initialize FastAPI backend and React frontend.
2.  **Core Backend:** Implement STL upload, volume calculation, and pricing logic.
3.  **Frontend Viewer:** Build React component with `@react-three/fiber` to render STLs.
4.  **Database Integration:** Set up SQLite and CRUD operations for Jobs/Materials.
5.  **Bambu Integration:**
    *   Implement MQTT Client for status/control.
    *   Implement FTPS Client for file upload.
    *   Implement CLI Wrapper for slicing.
6.  **Admin Dashboard:** specific UI for managing the print queue.
7.  **Testing & Deployment:** Dockerize the application for easy deployment.
