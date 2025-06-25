import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import babel from '@rollup/plugin-babel';
import terser from '@rollup/plugin-terser';
import copy from 'rollup-plugin-copy';
import serve from 'rollup-plugin-serve';

const isDevelopment = process.env.NODE_ENV === 'development';

export default {
  input: 'card/roo-card.js',
  output: {
    file: 'dist/roo-card.js',
    format: 'es',
    sourcemap: isDevelopment
  },
  plugins: [
    resolve({
      browser: true,
      preferBuiltins: false
    }),
    commonjs(),
    babel({
      babelHelpers: 'bundled',
      exclude: 'node_modules/**',
      presets: [
        ['@babel/preset-env', {
          targets: {
            browsers: ['last 2 versions']
          },
          modules: false
        }]
      ]
    }),
    !isDevelopment && terser({
      format: {
        comments: false
      },
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }),
    copy({
      targets: [
        { 
          src: 'card/components/*', 
          dest: 'dist/components' 
        },
        { 
          src: 'card/services/*', 
          dest: 'dist/services' 
        },
        {
          src: '../README.md',
          dest: 'dist'
        }
      ]
    }),
    isDevelopment && serve({
      open: true,
      contentBase: 'dist',
      port: 8080
    })
  ].filter(Boolean),
  external: [],
  watch: {
    clearScreen: false
  }
};
