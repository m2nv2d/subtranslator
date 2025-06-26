# Frontend Components Overview

## Purpose

The frontend components provide a simple, intuitive web interface for subtitle translation. Built with vanilla HTML5, CSS3, and JavaScript (ES6+), the frontend focuses on ease of use while providing essential functionality for file upload, language selection, progress feedback, and file download.

## Internal Structure

```
src/templates/
└── index.html           # Jinja2 template with form interface

src/static/
├── css/
│   ├── style.css        # Main stylesheet (current)
│   └── style_new.css    # Alternative stylesheet
└── js/
    ├── app.js           # Main JavaScript logic (current)
    └── app_new.js       # Alternative JavaScript implementation
```

## Exposed Interface

### User Interface Components
- **File Upload Form**: Multi-part form for SRT file selection
- **Language Selector**: Dropdown populated from server configuration
- **Speed Mode Selector**: Processing speed options (normal/fast/mock)
- **Submit Button**: Initiates translation process
- **Status Display**: Real-time feedback during processing
- **Error Display**: User-friendly error messages

### Client-Server Communication
- **Form Submission**: Asynchronous POST requests to `/translate` endpoint
- **Progress Updates**: Status message updates during processing
- **File Download**: Automatic download trigger for translated files
- **Error Handling**: Display of server error responses

## Design Pattern

The frontend follows a **Progressive Enhancement** approach with **Unobtrusive JavaScript**:

- **Base Functionality**: Form works without JavaScript (basic HTML form submission)
- **Enhanced Experience**: JavaScript adds async processing and better UX
- **Graceful Degradation**: Fallback behavior when JavaScript is disabled
- **Separation of Concerns**: HTML structure, CSS presentation, JavaScript behavior

## Key Features

### User Experience
- **Single Page Application**: All functionality on one page without navigation
- **Real-time Feedback**: Status updates during file processing
- **Automatic Downloads**: Translated files download automatically when ready
- **Error Recovery**: Clear error messages with guidance for resolution
- **Responsive Design**: Works on desktop and mobile devices

### File Handling
- **Drag & Drop Support**: Enhanced file selection with drag-and-drop
- **File Validation**: Client-side validation before upload
- **Progress Indication**: Visual feedback during upload and processing
- **File Type Filtering**: Restricts selection to .srt files only

### Form Management
- **Dynamic Language Population**: Server-provided language options
- **Form State Management**: Button states and field enabling/disabling
- **Input Validation**: Client-side validation with server-side backup
- **Reset Functionality**: Clear form after successful processing

## Integration Points

### With FastAPI Backend
```html
<!-- Template receives server data -->
<select name="target_lang" required>
  {% for language in languages %}
    <option value="{{ language }}">{{ language }}</option>
  {% endfor %}
</select>
```

### With JavaScript Logic
```javascript
// Form submission handling
document.getElementById('translate-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    await handleFormSubmission();
});
```

### With CSS Styling
```html
<!-- Semantic HTML with CSS classes -->
<div id="status-message" class="status-message hidden"></div>
<button id="submit-button" class="submit-button">Translate</button>
```

## Technical Implementation

### HTML Structure (index.html)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Meta tags, title, CSS links -->
</head>
<body>
    <form id="translate-form" enctype="multipart/form-data">
        <input type="file" name="file" accept=".srt" required>
        <select name="target_lang" required>
            <!-- Server-populated options -->
        </select>
        <select name="speed_mode">
            <option value="normal" selected>Normal</option>
            <option value="fast">Fast</option>
            <option value="mock">Mock</option>
        </select>
        <button type="submit">Translate</button>
    </form>
    <div id="status-message"></div>
    <script src="/static/js/app.js"></script>
</body>
</html>
```

### JavaScript Logic (app.js)
```javascript
// Main functionality
async function handleFormSubmission() {
    const formData = new FormData(document.getElementById('translate-form'));
    
    try {
        showStatus('Processing...', 'info');
        disableForm();
        
        const response = await fetch('/translate', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            await handleSuccess(response);
        } else {
            await handleError(response);
        }
    } catch (error) {
        handleNetworkError(error);
    } finally {
        enableForm();
    }
}
```

### CSS Styling (style.css)
```css
/* Modern, responsive design */
.container {
    max-width: 600px;
    margin: 0 auto;
    padding: 20px;
}

.form-group {
    margin-bottom: 1rem;
}

.status-message {
    padding: 10px;
    border-radius: 4px;
    margin-top: 1rem;
}

.status-info { background-color: #d1ecf1; color: #0c5460; }
.status-error { background-color: #f8d7da; color: #721c24; }
.status-success { background-color: #d4edda; color: #155724; }
```

## User Workflow

### Successful Translation Flow
1. User visits application homepage
2. User selects SRT file from device
3. User chooses target language from dropdown
4. User optionally selects speed mode
5. User clicks "Translate" button
6. JavaScript prevents default form submission
7. Form data sent asynchronously to server
8. Status message shows "Processing..."
9. Server processes file and returns translated content
10. JavaScript triggers automatic file download
11. Status message shows "Translation completed successfully"
12. Form is reset for next translation

### Error Handling Flow
1. User submits form with invalid input
2. Client-side validation catches obvious errors
3. If validation passes, request sent to server
4. Server returns error status with descriptive message
5. JavaScript displays user-friendly error message
6. Form remains populated for user to correct issues
7. User can modify input and retry

## Best Practices

### Progressive Enhancement
```javascript
// Check for required features before enhancement
if (window.FormData && window.fetch) {
    // Enhanced behavior with modern APIs
    enhanceForm();
} else {
    // Fallback to basic form submission
    console.warn('Using fallback form submission');
}
```

### Error Handling
```javascript
// Comprehensive error handling
async function handleError(response) {
    try {
        const errorData = await response.json();
        showStatus(errorData.error || 'Translation failed', 'error');
    } catch (parseError) {
        showStatus('An unexpected error occurred', 'error');
    }
}
```

### User Feedback
```javascript
// Clear, actionable status messages
function showStatus(message, type) {
    const statusEl = document.getElementById('status-message');
    statusEl.textContent = message;
    statusEl.className = `status-message status-${type}`;
    statusEl.classList.remove('hidden');
}
```

## Accessibility Considerations

### Semantic HTML
- Proper form labels and input associations
- ARIA attributes for screen readers
- Semantic HTML elements (form, button, select)
- Logical tab order for keyboard navigation

### Visual Design
- High contrast colors for readability
- Clear focus indicators for keyboard users
- Responsive design for various screen sizes
- Loading indicators for processing states

### Error Communication
- Clear, descriptive error messages
- Error messages associated with relevant form fields
- Status messages announced to screen readers
- Visual and textual feedback for all actions

## Performance Considerations

### Loading Optimization
- Minimal external dependencies (no frameworks)
- Optimized CSS and JavaScript files
- Proper caching headers for static assets
- Progressive loading of non-critical resources

### User Experience
- Immediate feedback on form submission
- Non-blocking UI during processing
- Efficient file handling (no unnecessary reads)
- Responsive interactions with loading states

### Network Efficiency
- FormData API for efficient file uploads
- Streaming responses for large files
- Appropriate error handling for network issues
- Minimal redundant requests

## Browser Compatibility

### Modern Features Used
- FormData API for file uploads
- Fetch API for HTTP requests
- ES6+ JavaScript features (async/await, arrow functions)
- CSS Grid/Flexbox for layout
- File API for client-side file handling

### Fallback Support
- Graceful degradation for older browsers
- Basic form submission as fallback
- Progressive enhancement approach
- Feature detection before enhancement

## Security Considerations

### Client-Side Validation
- Input validation provides user feedback
- Not relied upon for security (server validates)
- File type restrictions guide user behavior
- Size limits prevent obviously oversized uploads

### XSS Prevention
- No dynamic HTML generation from user input
- Server-provided data properly escaped in templates
- Status messages use textContent (not innerHTML)
- No eval() or similar dynamic code execution

### CSRF Protection
- Forms use appropriate HTTP methods
- Server handles CSRF protection
- No sensitive operations performed via GET
- Proper content-type headers for requests