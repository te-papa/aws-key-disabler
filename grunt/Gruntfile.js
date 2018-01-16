/*global module:false*/
module.exports = function(grunt) {

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    bumpup: {
      file: 'package.json'
    },

    replace: {
      dist: {
        options: {
          patterns: [
            {
              match: 'buildversion',
              replacement: '<%= pkg.version %>'
            },
            {
              match: 'deploymentregion',
              replacement: '<%= pkg.key_disabler.lambda.deployment_region %>'
            },
            {
              match: 'serviceaccount',
              replacement: '<%= pkg.key_disabler.iam.serviceaccount %>'
            },
            {
              match: 'exclusiongroup',
              replacement: '<%= pkg.key_disabler.iam.exclusiongroup %>'

            },
            {
              match: 'emailreportto',
              replacement: '<%= pkg.key_disabler.email.report_to %>'
            },
            {
              match: 'emailregion',
              replacement: '<%= pkg.key_disabler.email.email_region %>'
            },
            {
              match: 'emailreportfrom',
              replacement: '<%= pkg.key_disabler.email.report_from %>'
            },
            {
              match: 'emailsendcompletionreport',
              replacement: '<%= pkg.key_disabler.email.send_completion_report %>'
            },
            {
              match: 'maskaccesskeylength',
              replacement: '<%= pkg.key_disabler.mask_accesskey_length %>'
            },
            {
              match: 'first_warning_num_days',
              replacement: '<%= pkg.key_disabler.keystates.first_warning.days %>'
            },
            {
              match: 'first_warning_message',
              replacement: '<%= pkg.key_disabler.keystates.first_warning.message %>'
            },
            {
              match: 'last_warning_num_days',
              replacement: '<%= pkg.key_disabler.keystates.last_warning.days %>'
            },
            {
              match: 'last_warning_message',
              replacement: '<%= pkg.key_disabler.keystates.last_warning.message %>'
            },
            {
              match: 'key_max_age_in_days',
              replacement: '<%= pkg.key_disabler.keystates.expired.days %>'
            },
            {
              match: 'key_expired_message',
              replacement: '<%= pkg.key_disabler.keystates.expired.message %>'
            },
            {
              match: 'key_young_message',
              replacement: '<%= pkg.key_disabler.keystates.young.message %>'
            }
          ]
        },
        files: [
          {expand: true, flatten: true, src: ['../lambda/src/RotateAccessKey.py'], dest: '../lambda/build/'}
        ]
      }
    },

    rename: {
      release: {
        files: [{
          src: ['../releases/AccessKeyRotationPackage.zip'],
          dest: '../releases/AccessKeyRotationPackage.<%= pkg.version %>.zip'
        }]
      }
    },

    exec: {
      create_lambda_policy: {
        cmd: './scripts/createLambdaAccessKeyRotationPolicy.sh "<%= pkg.key_disabler.iam.lambda.policyname %>" "<%= pkg.key_disabler.iam.lambda.rolename %>" <%= pkg.key_disabler.lambda.deployment_region %>'
      },
      package_lambda_function: {
        cmd: './scripts/createZipPackage.sh'
      },
      create_lambda_function: {
        cmd: './scripts/createLambdaFunction.sh AccessKeyRotationPackage.<%= pkg.version %>.zip <%= pkg.version %> "<%= pkg.key_disabler.lambda.function_name %>" "<%= pkg.key_disabler.iam.lambda.rolename %>" <%= pkg.key_disabler.lambda.timeout %> <%= pkg.key_disabler.lambda.memory %> <%= pkg.key_disabler.lambda.deployment_region %>'
      },
      create_scheduled_event: {
        cmd: './scripts/createScheduledEvent.sh "<%=pkg.key_disabler.lambda.function_name %>" "<%= pkg.key_disabler.lambda.schedule.rulename %>" "<%= pkg.key_disabler.lambda.schedule.description %>" "<%= pkg.key_disabler.lambda.schedule.expression %>" <%= pkg.key_disabler.aws_account_number %> <%= pkg.key_disabler.lambda.deployment_region %>'
      },
    }

  });

  // Load NPM grunt tasks
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-exec');
  grunt.loadNpmTasks('grunt-replace');
  grunt.loadNpmTasks('grunt-contrib-rename');
  grunt.loadNpmTasks('grunt-bumpup');

  // Default task.
  //grunt.registerTask('default', 'watch');

  grunt.registerTask('build', ['replace']);
  grunt.registerTask('renamePackage', 'rename:release');

  grunt.registerTask('createLambdaPolicy', 'exec:create_lambda_policy');
  grunt.registerTask('packageLambdaFunction', 'exec:package_lambda_function');
  grunt.registerTask('createLambdaFunction', 'exec:create_lambda_function');
  grunt.registerTask('createScheduledEvent', 'exec:create_scheduled_event');

  grunt.registerTask('deployLambda', ['build', 'exec:package_lambda_function', 'renamePackage', 'exec:create_lambda_policy', 'exec:create_lambda_function', 'exec:create_scheduled_event']);
};
