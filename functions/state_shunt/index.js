const PubSub = require(`@google-cloud/pubsub`);
const pubsub = new PubSub();

/**
 * State events come across on their own topic, but it would also be nice
 * to be able to process them using the same topic as regular messages.
 * This function just adds a subFolder attribute to the message and sends
 * along on the other topic. Logic later down the pipe can look for this
 * and handle appropriately. This has no impact on the device-side exchange,
 * purely the back-end processing (namely schema validator).
 */
exports.state_shunt = event => {
  const attributes = event.attributes;
  const dataBuffer = Buffer.from(event.data, 'base64');
  const payload = JSON.parse(dataBuffer.toString('utf8'));

  attributes.subFolder = 'state';

  publishPubsubMessage('target', payload, attributes);
};

function publishPubsubMessage(topicName, data, attributes) {
  const dataBuffer = Buffer.from(JSON.stringify(data));

  pubsub
    .topic(topicName)
    .publisher()
    .publish(dataBuffer, attributes)
    .then(messageId => {
      //console.info(`Message ${messageId} published.`);
    })
    .catch(err => {
      console.error('Publishing error:', err);
    });
}
