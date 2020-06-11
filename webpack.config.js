
const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = {
    entry: path.resolve(__dirname, './tmv/style/custom.scss'),
    output: {
        path: path.resolve(__dirname, './tmv/static/dash'),
    },
    plugins: [
        new MiniCssExtractPlugin({
            filename: '[name].css',
            chunkFilename: '[id].css',
        }),
    ],
    module: {
      rules: [
        {
            test: /\.scss$/,
            use:  [
                {
                    loader: MiniCssExtractPlugin.loader,
                },
                'css-loader',
                'sass-loader',
                'postcss-loader',
            ],
        },
        {
            test: /\.(woff|woff2|eot|ttf|otf)$/,
            use: [
            'file-loader',
            ],
        },
      ],
    },
    devServer: {
      host: '0.0.0.0',
    }
  };
