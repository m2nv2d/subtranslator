# App JavaScript Module

## Module Overview
- **Purpose and responsibilities**: Client-side form handling, drag-and-drop file upload, progress tracking, AJAX communication, and user interface interactions
- **Design pattern used**: Event-driven programming with modern JavaScript (ES6+), progressive enhancement, and separation of concerns
- **Integration points**: HTML template elements, FastAPI backend endpoints, browser APIs (File API, Fetch API, DOM API)

## 🔍 Abstraction-Level Reference

### Module Initialization

#### DOMContentLoaded Event Handler
**Signature**: `document.addEventListener('DOMContentLoaded', () => { ... })`  
**Description**: Main module initialization that sets up all event listeners and validates required DOM elements  
**Pattern**: Ensures DOM is fully loaded before executing JavaScript functionality

**Element References**:
```javascript
const translateForm = document.getElementById('translate-form');
const fileInput = document.getElementById('file-input');
const targetLangSelect = document.getElementById('target-lang');
const speedModeSelect = document.getElementById('speed-mode');
const submitButton = document.getElementById('submit-button');
const progressContainer = document.getElementById('progress-container');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');
```

**Error Handling**: Validates all required elements exist, shows alert and returns early if any are missing

### Drag-and-Drop Functionality

#### Drop Zone Setup
**Element**: `.border-dashed` selector  
**Description**: Configures drag-and-drop functionality for the file upload area  

**Event Handlers**:
- `dragenter` - Triggered when dragged item enters drop zone
- `dragover` - Triggered while dragged item is over drop zone  
- `dragleave` - Triggered when dragged item leaves drop zone
- `drop` - Triggered when item is dropped

**Event Prevention**:
```javascript
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}
```
**Purpose**: Prevents browser default drag-and-drop behavior (like opening files)

#### Visual Feedback
**Drag Enter/Over States**:
```javascript
dropZone.classList.add('border-slate-500');
dropZone.classList.add('bg-slate-50');
```

**Drag Leave/Drop States**:
```javascript
dropZone.classList.remove('border-slate-500');
dropZone.classList.remove('bg-slate-50');
```

**Purpose**: Provides visual feedback when files are dragged over the drop zone

#### File Drop Handler
**Signature**: `dropZone.addEventListener('drop', (e) => { ... })`  
**Description**: Processes dropped files and updates the file input  

**File Processing**:
```javascript
const dt = e.dataTransfer;
const files = dt.files;
if (files.length) {
    fileInput.files = files;
    const fileName = files[0].name;
    if (fileName) {
        updateFileDisplay(fileName);
    }
}
```

**Behavior**: Takes first dropped file, assigns to file input, updates display

### File Input Handling

#### File Selection Event
**Signature**: `fileInput.addEventListener('change', () => { ... })`  
**Description**: Handles file selection via traditional file picker  

**File Processing**:
```javascript
if (fileInput.files.length) {
    updateFileDisplay(fileInput.files[0].name);
}
```

#### updateFileDisplay Function
**Signature**: `function updateFileDisplay(fileName)`  
**Description**: Updates the drop zone display text to show selected filename  

**Parameters**:
- `fileName: string` - Name of the selected file

**DOM Manipulation**:
```javascript
const fileNameDisplay = dropZone.querySelector('p.text-slate-600');
if (fileNameDisplay) {
    fileNameDisplay.textContent = fileName;
}
```

**Purpose**: Provides user feedback about which file has been selected

### Status Display System

#### showStatus Function
**Signature**: `function showStatus(message, type)`  
**Description**: Universal status display function that updates progress container with messages and visual states  

**Parameters**:
- `message: string` - Status message to display
- `type: string` - Status type ('processing', 'success', 'error')

**Behavior**:
1. Makes progress container visible
2. Updates progress text with message
3. Sets progress bar color and width based on type

**Status Type Mappings**:
```javascript
case 'processing':
    progressBar.className = 'h-full bg-blue-500 rounded-full';
    progressBar.style.width = '25%';
    break;
case 'success':
    progressBar.className = 'h-full bg-green-500 rounded-full';
    progressBar.style.width = '100%';
    break;
case 'error':
    progressBar.className = 'h-full bg-red-500 rounded-full';
    progressBar.style.width = '100%';
    break;
```

**Side Effects**: Modifies DOM elements to show progress state

### Form Submission Handling

#### Form Submit Event Handler
**Signature**: `translateForm.addEventListener('submit', async (event) => { ... })`  
**Description**: Main form submission handler with comprehensive validation, AJAX processing, and file download  

**Event Handling**:
```javascript
event.preventDefault(); // Prevent default synchronous submission
```

### Client-Side Validation

#### File Validation
**File Presence Check**:
```javascript
if (!fileInput.files || fileInput.files.length === 0) {
    showStatus('Error: Please select an SRT file.', 'error');
    return;
}
```

**File Type Validation**:
```javascript
const file = fileInput.files[0];
if (!file.name.toLowerCase().endsWith('.srt')) {
    showStatus('Error: Invalid file type. Please upload an SRT file.', 'error');
    return;
}
```

**Target Language Validation**:
```javascript
if (!targetLangSelect.value) {
    showStatus('Error: Please select a target language.', 'error');
    return;
}
```

**Error Conditions**:
- No file selected
- Non-SRT file type
- Missing target language selection

### AJAX Request Processing

#### FormData Preparation
**FormData Construction**:
```javascript
const formData = new FormData();
formData.append('file', file);
formData.append('target_lang', targetLangSelect.value);
formData.append('speed_mode', speedModeSelect.value);
```

**Purpose**: Prepares multipart form data for file upload

#### UI State Management
**Loading State**:
```javascript
submitButton.disabled = true;
showStatus('Uploading and translating... Please wait.', 'processing');
```

**Cleanup State** (in finally block):
```javascript
submitButton.disabled = false;
```

#### Fetch Request
**Request Configuration**:
```javascript
const response = await fetch('/translate', {
    method: 'POST',
    body: formData,
});
```

**Response Handling**:
- Success: Process blob response for file download
- Error: Parse JSON error message or use generic error

### File Download Processing

#### Success Response Handling
**Blob Processing**:
```javascript
if (response.ok) { // Status 200-299
    const blob = await response.blob();
    const originalFilename = file.name;
    const filenameBase = originalFilename.substring(0, originalFilename.lastIndexOf('.')) || originalFilename;
    const targetLang = targetLangSelect.value;
    const downloadFilename = `${filenameBase}_${targetLang}.srt`;
}
```

**Filename Generation**:
- Extracts base filename without extension
- Appends target language suffix
- Example: `movie.srt` + `Spanish` → `movie_Spanish.srt`

#### Download Trigger
**Temporary Link Creation**:
```javascript
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.style.display = 'none';
a.href = url;
a.download = downloadFilename;
document.body.appendChild(a);
a.click();
window.URL.revokeObjectURL(url); // Clean up the object URL
a.remove();
```

**Process**:
1. Creates object URL from blob
2. Creates temporary anchor element
3. Triggers download via programmatic click
4. Cleans up object URL and removes element

**Memory Management**: Properly revokes object URLs to prevent memory leaks

### Error Response Handling

#### HTTP Error Processing
**Status Code Handling**:
```javascript
if (response.ok) {
    // Success path
} else {
    // Error: Try to parse JSON error message from backend
    let errorMessage = `Request failed with status: ${response.status} ${response.statusText}`;
    try {
        const errorData = await response.json();
        if (errorData && errorData.error) {
            errorMessage = `Error: ${errorData.error}`;
        }
    } catch (jsonError) {
        console.error('Could not parse error response as JSON:', jsonError);
        // Keep the generic status text error message
    }
    showStatus(errorMessage, 'error');
}
```

**Error Message Priority**:
1. JSON error response from backend
2. HTTP status code and status text
3. Generic error message

#### Network Error Handling
**Fetch Exception Handling**:
```javascript
catch (error) {
    // Network error or other fetch issue
    console.error('Fetch error:', error);
    showStatus('Error: Could not connect to the server or process the request.', 'error');
}
```

**Error Types Covered**:
- Network connectivity issues
- CORS errors
- Request timeout
- Other fetch API failures

### Browser Compatibility

#### Modern JavaScript Features Used
- `async/await` - Asynchronous request handling
- `const/let` - Block-scoped variables
- Arrow functions - Concise function syntax
- Template literals - String interpolation
- Fetch API - Modern HTTP requests
- File API - File handling
- Object URL API - Blob downloads

#### Fallback Considerations
- Progressive enhancement from basic form submission
- Graceful degradation if JavaScript fails
- Error messaging for unsupported features

### Security Considerations

#### Client-Side Validation
**Purpose**: Provides immediate user feedback but never replaces server-side validation  
**Limitations**: Can be bypassed, so server-side validation is critical

#### File Type Validation
**Method**: Extension-based checking  
**Limitation**: Not comprehensive security (server validates content)

#### Error Information Disclosure
**Strategy**: Shows specific validation errors, generic server errors  
**Security**: Prevents information leakage about server internals

### Performance Considerations

#### Event Listener Efficiency
- Uses single event listeners rather than multiple handlers
- Proper event cleanup (though not needed for page-level listeners)
- Efficient DOM queries with early validation

#### Memory Management
- Revokes object URLs after download
- Removes temporary DOM elements
- Proper async/await usage for garbage collection

#### User Experience
- Immediate validation feedback
- Progress indication during processing
- Disabled submit button prevents double submission

### Tips/Notes
- **Progressive Enhancement**: Form works without JavaScript but enhanced with drag-and-drop and AJAX
- **File Handling**: Uses modern File API for drag-and-drop functionality
- **Error Handling**: Comprehensive error handling covers network, validation, and server errors
- **Accessibility**: Maintains form functionality for keyboard and screen reader users
- **Download UX**: Automatic file download with proper filename generation
- **State Management**: Clear visual feedback for all application states
- **Browser Support**: Uses modern JavaScript features, consider polyfills for older browsers
- **Security**: Client-side validation supplements but doesn't replace server-side security