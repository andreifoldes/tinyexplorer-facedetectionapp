module.exports = {
    babel: {
        plugins: [
            '@babel/plugin-transform-optional-chaining',
            '@babel/plugin-transform-nullish-coalescing-operator'
        ]
    },
    webpack: {
        configure: (webpackConfig) => {
            // Use electron-renderer target only when running in Electron context
            // For browser development, use web target
            const isElectron = process.env.ELECTRON_TARGET === 'true';
            
            if (isElectron) {
                webpackConfig.target = 'electron-renderer';
            } else {
                webpackConfig.target = 'web';
            }
            
            return webpackConfig;
        }
    }
};
