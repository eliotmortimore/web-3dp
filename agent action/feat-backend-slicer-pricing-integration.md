# Feature: Backend Slicer, Pricing & Printer Integration

## Context
Implemented a two-stage slicing workflow (Instant Quote vs. Production Slice) and integrated the pricing engine with real filament costs. Also updated the frontend to support these workflows and fixed various upload/display issues.

## Changes

### Backend
*   **New `EstimationService` (`backend/app/services/estimation.py`):**
    *   Uses `trimesh` to calculate volume, weight, and estimated print time instantly.
    *   Handles `trimesh.Scene` and invalid meshes gracefully.
*   **New `PricingService` (`backend/app/services/pricing.py`):**
    *   Centralized pricing logic based on material density and cost per kg (e.g., PLA $20/kg).
    *   Includes machine hourly rate ($3/hr) and setup fee ($5).
*   **Updated `BambuSlicer` (`backend/app/services/slicer.py`):**
    *   Refactored to be a "Production Slicer" triggered only by Admins.
    *   Wraps `BambuStudio` CLI to generate `.3mf` with G-code.
*   **Updated `BambuPrinter` (`backend/app/services/bambu_client.py`):**
    *   Implemented FTPS upload logic for secure file transfer to the printer.
    *   Updated MQTT payload structure to correctly start print jobs.
*   **API Endpoints (`backend/app/api/endpoints.py`):**
    *   `POST /upload`: Now synchronous. Uses `EstimationService` + `PricingService` for instant quotes. Uses `upsert=true` with retry logic for Supabase uploads.
    *   `PATCH /jobs/{id}`: New endpoint to update job details (qty, material) and recalculate price.
    *   `POST /jobs/{id}/slice`: Admin-only trigger for real slicing.
    *   `POST /jobs/{id}/approve`: Admin-only trigger to send the sliced file to the physical printer.

### Frontend
*   **Home / Quote (`Home.tsx`, `QuotePanel.tsx`):**
    *   Fixed upload logic (removed manual Content-Type header).
    *   Displayed price immediately after upload (no more infinite polling for estimation).
    *   "Add to Order" now finalizes the job via `PATCH` request.
*   **Admin Dashboard (`JobDetailsModal.tsx`):**
    *   Added "Slice / Prepare" button to trigger backend slicing.
    *   Added "Send to Printer" button (active after slicing).
    *   Added "Download" button for manual review.
    *   Integrated 3D viewer fixes (ShadowMap deprecation, TypeScript errors).
*   **3D Viewer (`Viewer3D.tsx`, `ModelViewer.tsx`):**
    *   Fixed Three.js deprecation warnings (ShadowMap).
    *   Fixed `STLLoader` imports and type definitions.

## Usage
1.  **User:** Uploads STL -> Gets instant price -> Clicks "Add to Order".
2.  **Admin:** Sees job -> Clicks "Slice / Prepare" -> Reviews result -> Clicks "Send to Printer".
