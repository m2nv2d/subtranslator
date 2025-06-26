# Index Template Module

## Module Overview
- **Purpose and responsibilities**: Main HTML template that renders the SRT translation upload interface with file selection, language options, and progress feedback
- **Design pattern used**: Server-side template rendering with Jinja2, progressive enhancement with JavaScript, and responsive design patterns
- **Integration points**: FastAPI backend for form submission, static assets (CSS/JS), and template context from translate router

## 🔍 Abstraction-Level Reference

### Template Structure

#### Document Head Configuration
**Purpose**: Sets up page metadata, styling, and external dependencies  
**Components**:
- Meta tags for responsive design and character encoding
- External font loading (Inter, Roboto Mono, Material Icons)
- Tailwind CSS CDN with forms and container-queries plugins
- Custom CSS for font configurations and Material Icons
- Favicon reference

**Font Stack**:
```css
.font-roboto-mono {
    font-family: "Roboto Mono", monospace;
}
```

**External Dependencies**:
- Tailwind CSS: `https://cdn.tailwindcss.com?plugins=forms,container-queries`
- Google Fonts: Inter (400,500,700,900) and Roboto Mono (400,500,700)
- Material Icons: `https://fonts.googleapis.com/icon?family=Material+Icons`

#### Layout Container
**Element**: `<div class="relative flex size-full min-h-screen flex-col group/design-root overflow-x-hidden">`  
**Description**: Root layout container using Flexbox for full-height layout  
**Design Pattern**: CSS Grid/Flexbox hybrid for responsive layout

**Structure**:
- Header with branding
- Main content area (flex-1 for expansion)
- Footer with copyright

### Header Section
**Element**: `<header class="border-b border-slate-200 p-4">`  
**Description**: Application header with branding and navigation  

**Components**:
- Translate icon (`material-icons`)
- Application title: "SRT Translator"
- Centered layout with max-width constraint (max-w-3xl)

**Styling**: Slate color scheme with subtle border separation

### Main Content Area

#### Form Container
**Element**: `<section class="border border-slate-200 rounded-lg bg-white p-6 shadow-sm">`  
**Description**: Primary form container with card-like styling  
**Max Width**: `max-w-lg` for optimal form readability

#### Form Element
**Element**: `<form id="translate-form" enctype="multipart/form-data">`  
**Description**: Main translation form with multipart encoding for file uploads  
**Method**: POST (handled by JavaScript)  
**Action**: `/translate` endpoint

**Form Fields**:
1. File upload with drag-and-drop
2. Target language selection
3. Speed mode selection
4. Progress indicator
5. Submit button

### File Upload Section

#### Drop Zone
**Element**: `<div class="border-2 border-dashed border-slate-300 rounded-md p-8 text-center hover:border-slate-400 transition-colors">`  
**Description**: Drag-and-drop file upload area with visual feedback  

**Components**:
- Upload file icon (`upload_file` Material Icon)
- Instructional text for drag-and-drop
- File selection button
- Hidden file input

**Interactive States**:
- Default: `border-slate-300`
- Hover: `border-slate-400`
- Drag active: `border-slate-500` + `bg-slate-50` (via JavaScript)

**File Input**:
```html
<input type="file" id="file-input" name="file" accept=".srt" required class="hidden">
```
- Hidden input with SRT file restriction
- Required field validation

### Form Controls Section

#### Target Language Selection
**Element**: `<select id="target-lang" name="target_lang" required>`  
**Description**: Dropdown for selecting translation target language  
**Template Logic**: Populated via Jinja2 template variables

**Jinja2 Integration**:
```html
{% for lang in languages %}
    {% if loop.first %}
    <option value="{{ lang }}" selected>{{ lang }}</option>
    {% else %}
    <option value="{{ lang }}">{{ lang }}</option>
    {% endif %}
{% endfor %}
```

**Behavior**:
- First language automatically selected
- Required field validation
- Styled with Tailwind form utilities

#### Speed Mode Selection
**Element**: `<select id="speed-mode" name="speed_mode">`  
**Description**: Toggle between translation speed modes  

**Options**:
- `normal` - Standard translation quality
- `fast` - Faster translation (selected by default)

**Default**: Fast mode for better user experience

#### Progress Indicator
**Container**: `<div id="progress-container" class="pt-2 hidden">`  
**Description**: Hidden progress display shown during translation  

**Components**:
- Progress bar with dynamic width and color
- Progress text with percentage and status
- Initially hidden (`hidden` class)

**Progress Bar Structure**:
```html
<div class="h-1.5 w-full rounded-full bg-slate-200 overflow-hidden">
    <div id="progress-bar" class="h-full bg-slate-600 rounded-full" style="width: 0%;"></div>
</div>
```

**Progress Text**:
```html
<p id="progress-text" class="text-slate-500 text-xs text-right mt-1.5">0% Translated</p>
```

### Submit Button
**Element**: `<button id="submit-button" type="submit">`  
**Description**: Form submission trigger with loading state management  

**States**:
- Default: "Translate File"
- Loading: Disabled via JavaScript
- Styled with full-width layout and focus states

**Styling**: 
- `bg-slate-800 hover:bg-slate-900` - Dark theme
- `focus:ring-2 focus:ring-slate-500` - Accessibility focus indicator

### Footer Section
**Element**: `<footer class="text-center p-4 text-xs text-slate-500 border-t border-slate-200">`  
**Description**: Simple copyright footer with year display  
**Content**: "© 2025 SRT Translator"

### Template Context Integration

#### Server-Side Variables
**Variable**: `languages`  
**Type**: List of strings  
**Source**: `settings.TARGET_LANGUAGES` from FastAPI backend  
**Usage**: Populates target language dropdown options

**Template Rendering**:
```python
return templates.TemplateResponse(
    "index.html",
    {"request": request, "languages": settings.TARGET_LANGUAGES}
)
```

### JavaScript Integration
**Script**: `/static/js/app.js`  
**Loading**: Deferred until after DOM content  
**Purpose**: Handles form interactions, drag-and-drop, progress updates, and AJAX submission

### CSS Integration
**Stylesheet**: Embedded Tailwind CSS + custom styles  
**Fallback**: `/static/css/style.css` for non-CDN scenarios  
**Design System**: Consistent slate color palette

### Accessibility Features

#### Form Accessibility
- Proper label associations (`for` attributes)
- Required field indicators
- Focus management with visible focus rings
- Semantic HTML structure

#### Keyboard Navigation
- All interactive elements are keyboard accessible
- Logical tab order through form fields
- Submit button accessible via Enter key

#### Screen Reader Support
- Semantic HTML elements (`<main>`, `<header>`, `<footer>`)
- Descriptive alt text for icons (Material Icons)
- Form labels properly associated with inputs

### Responsive Design

#### Breakpoint Strategy
- Mobile-first approach with Tailwind utilities
- Max-width constraints for readability
- Flexible layout containers

#### Layout Adaptation
- `md:py-12` - Increased padding on medium screens
- `max-w-lg` - Constrained form width for optimal UX
- `flex-1` - Expandable main content area

### Performance Considerations

#### Resource Loading
- Preconnect to Google Fonts for faster loading
- CDN-based Tailwind CSS for caching benefits
- Deferred JavaScript loading

#### Critical Path Optimization
- Inline critical CSS for above-the-fold content
- Async font loading with display swap
- Minimal render-blocking resources

### Tips/Notes
- **Progressive Enhancement**: Form works without JavaScript, enhanced with client-side features
- **Error Handling**: Visual feedback through progress indicator color changes
- **File Validation**: Client-side validation complemented by server-side validation
- **User Experience**: Drag-and-drop provides modern file upload experience
- **Maintainability**: Tailwind utility classes provide consistent styling
- **Security**: Form uses proper enctype for secure file uploads
- **Customization**: Material Icons and consistent color scheme provide professional appearance