    'use strict';

    angular.module('app')
        .config(function ($stateProvider) {
            $stateProvider
                .state('commissions', {
                    parent: 'account',
                    url: '/commissions',
                    data: {
                        authorities: [],
                        pageTitle: 'register.title'
                    },
                    views: {
                        'content@': {
                            templateUrl: '/views/book/list.html',
                            controller: 'BookController'
                        }
                    }/*,
                    resolve: {
                        translatePartialLoader: ['$translate', '$translatePartialLoader', function ($translate, $translatePartialLoader) {
                            $translatePartialLoader.addPart('register');
                            return $translate.refresh();
                        }]
                    }*/
                }).state('add-commission', {
                parent: 'account',
                url: '/add-commission/{id}',
                data: {
                    authorities: []
                },
                views: {
                    'content@': {
                        templateUrl: '/views/book/add.html',
                        controller: 'BookAddController'
                    }
                }
            })
        });
