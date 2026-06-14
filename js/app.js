var app=angular.module('app', ['LocalStorageModule', 'pascalprecht.translate', 'tmh.dynamicLocale',
    'ui.bootstrap', // for modal dialogs
    'ngResource', 'ui.router', 'ngCookies','ngFileUpload']);

app.run(function ($rootScope, $location, $window, $http, $state, $translate, Language) {

    $rootScope.fieldKey == 'Bangla'
    $rootScope.$on('$stateChangeStart', function (event, toState, toStateParams) {
        $rootScope.toState = toState;
        $rootScope.toStateParams = toStateParams;
        // if (Principal.isIdentityResolved()) {
        //     Auth.authorize();
        // }
        console.log('finish');
        console.log(toState);
        Language.getCurrent().then(function (language) {
            console.log(language)
            $translate.use(language);
        });

    });
    var updateTitle = function(titleKey) {
        if (!titleKey && $state.$current.data && $state.$current.data.pageTitle) {
            titleKey = $state.$current.data.pageTitle;
        }
        $translate(titleKey || 'global.title').then(function (title) {
            $window.document.title = title;
        });
    };


    $rootScope.$on('$stateChangeSuccess',  function(event, toState, toParams, fromState, fromParams) {
        var titleKey = 'Title' ;
        updateTitle(titleKey);
        $rootScope.$on('$translateChangeSuccess', function() { updateTitle(); });
        console.log('finish');
        console.log(toState);
        console.log(fromState);
    });

    $rootScope.$on('$stateChangeError',  function(event, toState, toParams, fromState, fromParams,error) {
        console.log(error);
    });

    // if the current translation changes, update the window title
    // $rootScope.$on('$translateChangeSuccess', function() { updateTitle(); });


    $rootScope.back = function() {
        // If previous state is 'activate' or do not exist go to 'home'
        if ($rootScope.previousStateName === 'activate' || $state.get($rootScope.previousStateName) === null) {
            $state.go('dashboard');
        } else {
            console.log($rootScope.previousStateName)
            console.log($rootScope.previousStateParams)
            if(!$rootScope.previousStateName) {
                $state.go('dashboard');
            }
            if($rootScope.previousStateName && $rootScope.previousStateParams) {
                $state.go($rootScope.previousStateName, $rootScope.previousStateParams);
            }

        }
    };
    $rootScope.closeAlert = function() {
        $('.message.error, .message.success, .message.warning').hide();
        $rootScope.globalErrorMessage = '';
        $rootScope.globalSuccessMessage = '';
        $rootScope.globalWarningMessage = '';
    }
    $rootScope.setErrorMessage = function (message) {
        $rootScope.closeAlert();
        $('.message.error').show();
        localStorage.setItem('globalErrorMessage', message);
        $rootScope.globalErrorMessage= localStorage.getItem('globalErrorMessage');
        setTimeout(function() { $(".message.error").hide(); }, 2000);
    }
    $rootScope.setFile = function ($file) {
        var  attachment = {};
        try {
            if ($file) {
                var fileReader = new FileReader();
                fileReader.readAsDataURL($file);
                fileReader.onload = function (e) {
                    var base64Data = e.target.result.substr(e.target.result.indexOf('base64,') + 'base64,'.length);
                    try {
                        attachment.file = base64Data;
                        attachment.fileContentType = $file.type;
                        attachment.fileName = $file.name;
                        attachment.showAddMore = true;
                    } catch (e) {
                        console.log("file upload error.....")
                        console.log(e)
                    }
                };

            }
        } catch (e) {
            console.log("file upload error.....")
            console.log(e)
        }
        return attachment;
    };
    $rootScope.b64toBlob = function b64toBlob(b64Data, contentType, sliceSize) {
        contentType = contentType || '';
        sliceSize = sliceSize || 512;

        var byteCharacters = atob(b64Data);
        var byteArrays = [];

        for (var offset = 0; offset < byteCharacters.length; offset += sliceSize) {
            var slice = byteCharacters.slice(offset, offset + sliceSize);

            var byteNumbers = new Array(slice.length);
            for (var i = 0; i < slice.length; i++) {
                byteNumbers[i] = slice.charCodeAt(i);
            }

            var byteArray = new Uint8Array(byteNumbers);

            byteArrays.push(byteArray);
        }

        var blob = new Blob(byteArrays, {type: contentType});
        return blob;
    };

    $rootScope.previewImage = function (content, contentType, name) {
        var blob = $rootScope.b64toBlob(content, contentType);
        $rootScope.viewerObject.content = (window.URL || window.webkitURL).createObjectURL(blob);
        $rootScope.viewerObject.contentType = contentType;
        $rootScope.viewerObject.pageTitle = name;
        // call the modal
        $rootScope.showFilePreviewModal();
    };
    $rootScope.getObjectValue = function (object,fieldName) {
        // console.log(fieldName+'_bangla')
        if ($rootScope.languageKey == 'bn') {
            return object[fieldName+'_bangla'];
            console.log(object[fieldName+'_bangla']);
        } else {
            return object[fieldName];
        }
        return object[fieldName];
    };

    $rootScope.viewerObject = {};
    $rootScope.showFilePreviewModal = function()
    {
        $modal.open({
            templateUrl: '/views/common-file-viewer.html',
            controller: [
                '$scope', '$modalInstance', function($scope, $modalInstance) {
                    $scope.ok = function() {
                        $rootScope.viewerObject = {};
                        $modalInstance.close();
                    };
                    $scope.closeModal = function() {
                        $rootScope.viewerObject = {};
                        $modalInstance.dismiss();
                    };
                }
            ]
        });
    };

    $rootScope.confirmationObject = {};
    $rootScope.showConfirmation = function()
    {
        $modal.open({
            templateUrl: 'static/views/common-confirmation.html',
            controller: [
                '$scope', '$modalInstance', function($scope, $modalInstance) {
                    $scope.ok = function() {
                        $rootScope.confirmationObject = {};
                        $modalInstance.close();
                    };
                    $scope.closeModal = function() {
                        $rootScope.confirmationObject = {};
                        $modalInstance.dismiss();
                    };
                }
            ]
        });
    };

    $rootScope.setSuccessMessage = function (message) {
        $rootScope.closeAlert();
        $('.message.success').show();
        localStorage.setItem('globalSuccessMessage',message);
        $rootScope.globalSuccessMessage= localStorage.getItem('globalSuccessMessage');
        setTimeout(function() { $(".message.success").hide(); }, 2000);
    };

    $rootScope.searchByTrackID = false;

    $rootScope.logout = function () {
        Auth.logout();
        $state.go('home');
    };
})
    .config(function ($stateProvider, $urlRouterProvider, $httpProvider,$translateProvider, $locationProvider, tmhDynamicLocaleProvider) {
        // uncomment below to make alerts look like toast
        //AlertServiceProvider.showAsToast(true);

        //enable CSRF
        $httpProvider.defaults.xsrfCookieName = 'CSRF-TOKEN';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRF-TOKEN';

        //Cache everything except rest api requests
        /*httpRequestInterceptorCacheBusterProvider.setMatchlist([/.*api.*!/, /.*protected.*!/], true);*/

        $urlRouterProvider.otherwise('/');
        $stateProvider.state('site', {
            'abstract': true,
            views: {
                'navbar@': {
                    templateUrl: '/views/navbar.html',
                    controller: 'NavbarController'
                }
            },
            resolve: {
                translatePartialLoader: ['$translate', '$translatePartialLoader', function ($translate, $translatePartialLoader) {
                    $translatePartialLoader.addPart('global');
                    return $translate.refresh();
                }]
            }
        });

        $httpProvider.interceptors.push('errorHandlerInterceptor');
        $httpProvider.interceptors.push('authExpiredInterceptor');
        /* $httpProvider.interceptors.push('notificationInterceptor');*/

        $translateProvider.useLoader('$translatePartialLoader', {
            urlTemplate: './i18n/{lang}/{part}.json'
        });
        $translateProvider.preferredLanguage('bn');
        $translateProvider.useCookieStorage();
        $translateProvider.useSanitizeValueStrategy('escaped');
        $translateProvider.addInterpolation('$translateMessageFormatInterpolation');

        tmhDynamicLocaleProvider.localeLocationPattern('https://cdn.jsdelivr.net/npm/angular-i18n@1.5.8/angular-locale_{{locale}}.js');
        tmhDynamicLocaleProvider.useCookieStorage();
        tmhDynamicLocaleProvider.storageKey('NG_TRANSLATE_LANG_KEY');

    })
    .config(['$urlMatcherFactoryProvider', function($urlMatcherFactory) {
        $urlMatcherFactory.type('boolean', {
            name : 'boolean',
            decode: function(val) { return val == true ? true : val == "true" ? true : false },
            encode: function(val) { return val ? 1 : 0; },
            equals: function(a, b) { return this.is(a) && a === b; },
            is: function(val) { return [true,false,0,1].indexOf(val) >= 0 },
            pattern: /bool|true|0|1/
        });
    }]);


