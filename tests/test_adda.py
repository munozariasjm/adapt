"""
Test functions for adda module.
"""


import numpy as np
import tensorflow as tf
from tensorflow.keras import Sequential, Model
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam

from adapt.feature_based import ADDA

Xs = np.concatenate((
    np.linspace(0, 1, 100).reshape(-1, 1),
    np.zeros((100, 1))
    ), axis=1)
Xt = np.concatenate((
    np.linspace(0, 1, 100).reshape(-1, 1),
    np.ones((100, 1))
    ), axis=1)
ys = 0.2 * Xs[:, 0].ravel()
yt = 0.2 * Xt[:, 0].ravel()


def _get_encoder(input_shape=Xs.shape[1:]):
    model = Sequential()
    model.add(Dense(1, input_shape=input_shape,
                    kernel_initializer="ones",
                    use_bias=False))
    model.compile(loss="mse", optimizer="adam")
    return model


def _get_discriminator(input_shape=(1,)):
    model = Sequential()
    model.add(Dense(10,
                    input_shape=input_shape,
                    activation="relu"))
    model.add(Dense(1,
                    activation="sigmoid"))
    model.compile(loss="mse", optimizer="adam")
    return model


def _get_task(input_shape=(1,), output_shape=(1,)):
    model = Sequential()
    model.add(Dense(np.prod(output_shape),
                    use_bias=False,
                    input_shape=input_shape))
    model.compile(loss="mse", optimizer=Adam(0.1))
    return model


def test_fit():
    tf.random.set_seed(0)
    np.random.seed(0)
    model = ADDA(_get_encoder(),
                 _get_task(), _get_discriminator(), pretrain__epochs=100,
                 loss="mse", optimizer=Adam(0.01), metrics=["mae"])
    model.fit(Xs, ys, Xt, yt,
              epochs=10, batch_size=34, verbose=0)
    assert isinstance(model, Model)
    # assert model.encoder_src_.get_weights()[0][1][0] == 1.0
    assert np.abs(model.encoder_.get_weights()[0][1][0]) < 0.2
    # assert np.all(np.abs(model.encoder_.predict(Xt)) < 
    #               np.abs(model.encoder_src_.get_weights()[0][0][0]))
    # assert np.sum(np.abs(
    #     model.predict(Xt, "source").ravel() - yt)) > 10
    # assert np.sum(np.abs(
    #     model.predict(Xs, "source").ravel() - ys)) < 0.01
    assert np.sum(np.abs(np.ravel(model.predict_task(Xs, domain="src")) - ys)) < 11
    assert np.sum(np.abs(model.predict(Xt).ravel() - yt)) < 25
    
    
def test_nopretrain():
    tf.random.set_seed(0)
    np.random.seed(0)
    encoder = _get_encoder()
    task = _get_task()
    
    src_model = Sequential()
    src_model.add(encoder)
    src_model.add(task)
    src_model.compile(loss="mse", optimizer=Adam(0.01))
    
    src_model.fit(Xs, ys, epochs=100, batch_size=34, verbose=0)
    
    Xs_enc = src_model.predict(Xs)
    
    model = ADDA(encoder, task, _get_discriminator(), pretrain=False,
                 loss="mse", optimizer=Adam(0.01), metrics=["mae"],
                 copy=False)
    model.fit(Xs_enc, ys, Xt, epochs=30, batch_size=34, verbose=0)
    assert np.abs(model.encoder_.get_weights()[0][1][0]) < 0.2
    assert np.sum(np.abs(np.ravel(model.predict(Xs)) - ys)) < 25
    assert np.sum(np.abs(model.predict(Xt).ravel() - yt)) < 25