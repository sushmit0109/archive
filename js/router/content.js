    'use strict';

    angular.module('app')
        .config(function ($stateProvider) {
            $stateProvider
                .state('contents', {
                    parent: 'account',
                    url: '/contents',
                    data: {
                        authorities: [],
                        pageTitle: 'register.title'
                    },
                    views: {
                        'content@': {
                            templateUrl: '/views/content/list.html',
                            controller: 'ContentController'
                        }
                    }/*,
                    resolve: {
                        translatePartialLoader: ['$translate', '$translatePartialLoader', function ($translate, $translatePartialLoader) {
                            $translatePartialLoader.addPart('register');
                            return $translate.refresh();
                        }]
                    }*/
                }).state('add-content', {
                parent: 'account',
                url: '/add-content/{id}',
                data: {
                    authorities: []
                },
                views: {
                    'content@': {
                        templateUrl: '/views/content/add.html',
                        controller: 'ContentAddController'
                    }
                }
            });
        });
