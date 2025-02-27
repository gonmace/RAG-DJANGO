module.exports = {
    content: [
        '../../templates/*.html',
        '../../templates/**/*.html', 
        '../../main/src/index-main.js',
        '../../**/templates/*.html',  
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
            mytheme: {
              // http://colormind.io/bootstrap/
              // https://coolors.co/1a281f-aaaaaa-cf5535-fec601-f6f8ff
              mytheme: {
                "primary": "#cf5535",  // Main brand color
                "secondary": "#fec601", // Light accent
                "accent": "#aaaaaa", // Dark accent
                "neutral": "#1a281f", // Dark shades
                "base-100": "#f6f8ff", // Light shades (background)
                "info": "#1E429F",
                "success": "#0E9F6E",
                "warning": "#C27803",
                "error": "#E02424"
              },
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
