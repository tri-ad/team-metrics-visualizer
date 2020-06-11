# tmv_dash_components

Custom Dash components for TMV.

The folder is generated via https://github.com/plotly/dash-component-boilerplate

## Building

1. Install dependencies: `npm i`
2. Build js and python: `pipenv run npm run build`
3. Now you can import components in the app via `import tmv_dash_components as tdc`

## Making new components

1. Create a new component file in `src/lib/components/`
2. Add an export to `src/lib/index.js`
3. Add the component to `src/demo/App.js`
4. Run `npm run start` and open http://127.0.0.1:8051 to see the demo app.
5. You can update the component's code and see changes in the demo app.
6. Once the component is ready, build it to use in the dashboard.
