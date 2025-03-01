module.exports = {
  content: [
      '../../templates/*.html',
      '../../templates/**/*.html', 
      '../../main/src/index-main.js',
      '../../**/templates/*.html',  
      '../../**/templates/**/*.html',
      '../../embeddings/templates/**/*.html', 
      '../../embeddings/forms.py', 
      '!../../**/node_modules',
  ],
  plugins: [
      require('daisyui'),
      require('@tailwindcss/forms'),
      require('@tailwindcss/typography'),
      require('@tailwindcss/aspect-ratio'),
  ],
  daisyui: {
      themes: [
        {
          
            // http://colormind.io/bootstrap/
            // https://coolors.co/1a281f-aaaaaa-cf5535-fec601-f6f8ff
            mytheme: {
              "primary": "#F19E2B",  // Main brand color
              "secondary": "#90a8a2", // Light accent
              "accent": "#CA5043", // Dark accent
              "neutral": "#364146", // Dark shades
              "base-100": "oklch(94% 0 0)", // Light shades (background)
              "info": "oklch(74% 0.16 232.661)",
              "success": "oklch(76% 0.177 163.223)",
              "warning": "oklch(90% 0.182 98.111)",
              "error": "oklch(70% 0.191 22.216)"
            },
          
        },
        "dark",
      ],
    },
    theme: {
      extend: {
        fontFamily: {
          'sans': ['nunito', 'sans-serif'],
        },
      },
    },
}


// @plugin "daisyui/theme" {
//   name: "bumblebee-gmc";
//   default: false;
//   prefersdark: false;
//   color-scheme: "light";
//   --color-base-100: oklch(100% 0 0);
//   --color-base-200: oklch(94% 0 0);
//   --color-base-300: oklch(87% 0 0);
//   --color-base-content: oklch(26% 0.007 34.298);
//   --color-primary: #F19E2B;
//   --color-primary-content: oklch(98% 0.003 247.858);
//   --color-secondary: #90a8a2;
//   --color-secondary-content: oklch(98% 0.003 247.858);
//   --color-accent: #CA5043;
//   --color-accent-content: oklch(98% 0.003 247.858);
//   --color-neutral: #364146;
//   --color-neutral-content: oklch(98% 0.003 247.858);
//   --color-info: oklch(74% 0.16 232.661);
//   --color-info-content: oklch(27% 0.033 256.848);
//   --color-success: oklch(76% 0.177 163.223);
//   --color-success-content: oklch(27% 0.033 256.848);
//   --color-warning: oklch(90% 0.182 98.111);
//   --color-warning-content: oklch(27% 0.033 256.848);
//   --color-error: oklch(70% 0.191 22.216);
//   --color-error-content: oklch(27% 0.033 256.848);
//   --radius-selector: 1rem;
//   --radius-field: 0.5rem;
//   --radius-box: 1rem;
//   --size-selector: 0.25rem;
//   --size-field: 0.25rem;
//   --border: 1px;
//   --depth: 1;
//   --noise: 0;
// }