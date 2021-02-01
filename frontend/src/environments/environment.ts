/* @TODO replace with your variables
 * ensure all variables on this page match your project
 */

export const environment = {
  production: false,
  apiServerUrl: 'http://127.0.0.1:4000', // the running FLASK api server url
  auth0: {
    url: 'ahumk.us.auth0.com', // the auth0 domain prefix
    audience: 'coffeshop', // the audience set for the auth0 app
    clientId: 'l63nH3g4NiYvBrBSRYvN3rgeIpltDJWP', // the client id generated for the auth0 app
    callbackURL: 'http://127.0.0.1:8100', // the base url of the running ionic application.
  }
};
