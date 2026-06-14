'use strict';

angular.module('app')
    .config(function ($stateProvider) {
        $stateProvider
            .state('home', {
                parent: 'site',
                url: '/{tid}',
                data: {
                    authorities: []
                },
                views: {
                    'content@': {
                        templateUrl: '/app/main/main.html',
                        controller: 'MainController'
                    }
                }
            })

         });
