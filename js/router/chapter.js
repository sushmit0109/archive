    'use strict';

    angular.module('app')
        .config(function ($stateProvider) {
            $stateProvider
                .state('commission-report', {
                parent: 'account',
                url: '/commission-report/{id}',
                data: {
                    authorities: []
                },
                views: {
                    'content@': {
                        templateUrl: '/views/preview-book.html',
                        controller: 'PreviewBookController'
                    }
                }
            }).state('summary-report', {
                parent: 'account',
                url: '/summary-report/',
                data: {
                    authorities: []
                },
                views: {
                    'content@': {
                        templateUrl: '/views/summary-report.html',
                        controller: 'SummaryReportController'
                    }
                }
            }).state('gallery', {
                parent: 'account',
                url: '/gallery',
                data: {
                    authorities: []
                },
                views: {
                    'content@': {
                        templateUrl: '/views/gallery.html',
                        controller: 'GalleryController'
                    }
                }
            });
        });
