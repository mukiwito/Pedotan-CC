from keras.models import load_model

# app = Flask(__name__)
# api = Api(app)

model = load_model('ai_model\content\crop_predNew.h5')

komoditas_class = ['apple', 'coffee', 'grapes', 'corn', 'rice']


new_data = [[90, 42, 43, 20.879744,	82.002744, 6.502985, 202.935536]]

def get_predicted_label_komoditas(pred_probabilities):
    """
    Turns an array of predictions probabilities into a label
    """
    return komoditas_class[pred_probabilities.argmax()]

def predict_komoditas():
    data = new_data
    pred = model.predict(data)
    max_pred = max(pred[0])
    pred_class = get_predicted_label_komoditas(pred[0])
    print(max_pred)
    print(pred_class)
    return {'predict': pred_class}, 200

predict_komoditas()