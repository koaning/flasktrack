# CSS Styling

This project uses Tailwind CSS via CDN for styling.

The Tailwind CSS script is loaded directly in the base templates:
- `/app/views/layouts/base.html`
- `/app/views/admin/base.html`

No custom CSS files are needed as Tailwind provides all necessary utility classes.

If you need custom styles in the future, you can:
1. Add a custom CSS file here
2. Link to it in the base templates
3. Or consider setting up a Tailwind build process for production optimization