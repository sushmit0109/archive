'use strict';

angular.module('app')
    .config(function ($stateProvider) {
        $stateProvider
            .state('sections', {
                parent: 'account',
                url: '/sections',
                data: {
                    authorities: [],
                    pageTitle: 'register.title'
                },
                views: {
                    'content@': {
                        templateUrl: '/views/section/list.html',
                        controller: 'SectionController'
                    }
                }
            }).state('add-section', {
            parent: 'account',
            url: '/add-section/{id}',
            data: {
                authorities: []
            },
            views: {
                'content@': {
                    templateUrl: '/views/section/add.html',
                    controller: 'SectionAddController'
                }
            }
        });
    });
