# Style CSS Module

## Module Overview
- **Purpose and responsibilities**: Provides fallback styling and custom CSS classes for the SRT translation interface when Tailwind CDN is unavailable
- **Design pattern used**: Progressive enhancement with CSS fallbacks, utility-first approach, and component-based status styling
- **Integration points**: HTML template elements, Tailwind CSS framework, and JavaScript status management system

## 🔍 Abstraction-Level Reference

### Fallback Base Styles

#### Body Element Styling
**Selector**: `body`  
**Description**: Provides core styling fallbacks when Tailwind CSS is unavailable  

**Properties**:
```css
body {
    font-family: "Roboto Mono", monospace;
    margin: 0;
    padding: 0;
    background-color: #f8fafc;
    color: #1e293b;
}
```

**Purpose**: Ensures consistent typography and color scheme without framework dependencies  
**Color Scheme**: Matches Tailwind's slate color palette  
**Typography**: Monospace font for technical application aesthetic

### Utility Classes

#### Hidden Class
**Selector**: `.hidden`  
**Description**: Utility class for hiding elements, overriding any conflicting styles  

**Implementation**:
```css
.hidden {
    display: none !important;
}
```

**Usage**: Applied to progress container and other elements that need to be hidden/shown dynamically  
**Importance**: Uses `!important` to ensure hiding takes precedence

### Status Message System

#### Processing Status
**Selector**: `.status-processing`  
**Description**: Styling for processing state messages  

**Properties**:
```css
.status-processing {
    color: #1e40af;
    background-color: #dbeafe;
    border-color: #bfdbfe;
}
```

**Color Scheme**: Blue color palette indicating active processing  
**Hierarchy**: Text (dark blue) → Background (light blue) → Border (medium blue)

#### Success Status
**Selector**: `.status-success`  
**Description**: Styling for successful completion messages  

**Properties**:
```css
.status-success {
    color: #15803d;
    background-color: #dcfce7;
    border-color: #bbf7d0;
}
```

**Color Scheme**: Green color palette indicating successful completion  
**Visual Pattern**: Consistent hierarchy with processing and error states

#### Error Status
**Selector**: `.status-error`  
**Description**: Styling for error state messages  

**Properties**:
```css
.status-error {
    color: #b91c1c;
    background-color: #fee2e2;
    border-color: #fecaca;
}
```

**Color Scheme**: Red color palette indicating errors or failures  
**Accessibility**: High contrast ratios for error visibility

### Form Element Styling

#### File Input Styling
**Selector**: `input[type="file"]`  
**Description**: Basic styling for file input elements  

**Properties**:
```css
input[type="file"] {
    width: 100%;
}
```

**Purpose**: Ensures file inputs take full width of their container  
**Responsive**: Adapts to container width for responsive design

#### Select Element Styling
**Selector**: `select`  
**Description**: Consistent styling for dropdown select elements  

**Properties**:
```css
select {
    padding: 0.5rem;
    border-radius: 0.375rem;
    border: 1px solid #cbd5e1;
}
```

**Design Details**:
- `padding: 0.5rem` (8px) - Comfortable touch target
- `border-radius: 0.375rem` (6px) - Rounded corners matching design system
- `border: 1px solid #cbd5e1` - Subtle border in slate gray

### Button Styling

#### Base Button Styles
**Selector**: `button`  
**Description**: Base styling for all button elements  

**Properties**:
```css
button {
    cursor: pointer;
}
```

**Purpose**: Ensures buttons have proper cursor indication for interactivity

#### Disabled Button States
**Selector**: `button:disabled`  
**Description**: Visual styling for disabled button states  

**Properties**:
```css
button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
```

**Visual Feedback**:
- `opacity: 0.5` - Dims button to indicate disabled state
- `cursor: not-allowed` - Shows appropriate cursor when hovering

**Accessibility**: Clear visual indication of disabled state for users

### Layout Fallback Styles

#### Layout Container
**Selector**: `.layout-container`  
**Description**: Flexbox layout fallback for main application structure  

**Properties**:
```css
.layout-container {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}
```

**Layout Pattern**: Full-height column layout with header, expandable main, and footer  
**Responsive**: Adapts to viewport height changes

#### Main Content Area
**Selector**: `main`  
**Description**: Styling for main content area with flexible growth  

**Properties**:
```css
main {
    flex: 1;
    padding: 1rem;
}
```

**Flex Behavior**: `flex: 1` allows main content to expand and fill available space  
**Spacing**: `1rem` (16px) padding provides consistent spacing

#### Footer Styling
**Selector**: `footer`  
**Description**: Styling for application footer with consistent appearance  

**Properties**:
```css
footer {
    text-align: center;
    padding: 1rem;
    border-top: 1px solid #e2e8f0;
    color: #64748b;
    font-size: 0.75rem;
}
```

**Design Elements**:
- `text-align: center` - Centered copyright text
- `border-top: 1px solid #e2e8f0` - Subtle separator line
- `color: #64748b` - Muted gray text color
- `font-size: 0.75rem` (12px) - Small text size for footer content

### Color Palette System

#### Slate Color Palette
The CSS uses a consistent slate color palette that matches Tailwind's color system:

**Primary Colors**:
- `#1e293b` - Dark slate for primary text  
- `#64748b` - Medium slate for secondary text
- `#cbd5e1` - Light slate for borders
- `#e2e8f0` - Very light slate for separators
- `#f8fafc` - Near-white slate for backgrounds

**Status Colors**:
- **Blue** (Processing): `#1e40af`, `#dbeafe`, `#bfdbfe`
- **Green** (Success): `#15803d`, `#dcfce7`, `#bbf7d0`  
- **Red** (Error): `#b91c1c`, `#fee2e2`, `#fecaca`

### Progressive Enhancement Strategy

#### Fallback Approach
**Primary Styling**: Tailwind CSS via CDN  
**Fallback Styling**: Custom CSS when CDN is unavailable  
**Design Consistency**: Fallback styles maintain similar visual appearance

#### CSS Cascade Strategy
- Tailwind utilities take precedence when available
- Custom CSS provides baseline functionality
- Specific utility classes (like `.hidden`) use `!important` when needed

### Responsive Design Support

#### Flexible Layout
- Uses percentage-based widths and flexbox for adaptability
- Consistent spacing with rem units for scalability
- Mobile-first approach with minimal media queries needed

#### Typography Scaling
- Uses rem units for relative sizing
- Consistent font families across all fallback styles
- Proper line height and spacing ratios

### Browser Compatibility

#### CSS Features Used
- **Flexbox**: Widely supported layout method
- **Border-radius**: Supported in all modern browsers
- **Opacity**: Universal support for transparency effects
- **CSS3 Colors**: Hex color values with universal support

#### Graceful Degradation
- Provides functional interface without modern CSS features
- Uses standard CSS properties for maximum compatibility
- No dependencies on CSS Grid or other advanced features

### Performance Considerations

#### CSS Optimization
- Minimal CSS file size for fast loading
- Uses efficient selectors without complex combinators
- Focuses on essential styles only

#### Caching Strategy
- Static CSS file can be cached by browsers
- Provides consistent styling independent of CDN availability
- Reduces dependency on external resources

### Maintenance and Extensibility

#### Style Organization
- Logical grouping of related styles
- Consistent naming conventions
- Clear separation between fallback and utility styles

#### Customization Points
- Color palette can be easily modified
- Spacing system uses consistent rem units
- Status styling follows predictable patterns

### Tips/Notes
- **CDN Fallback**: This stylesheet ensures functionality when Tailwind CDN is unavailable
- **Color Consistency**: Maintains visual consistency with Tailwind's slate color palette
- **Status System**: Provides clear visual feedback for different application states
- **Accessibility**: Ensures proper contrast ratios and disabled state indicators
- **Maintainability**: Organized structure makes it easy to add new fallback styles
- **Performance**: Lightweight CSS that loads quickly as a fallback
- **Progressive Enhancement**: Works with or without JavaScript and external frameworks