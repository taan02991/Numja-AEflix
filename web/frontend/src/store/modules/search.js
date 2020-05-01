
const state =  {
    transcribeMessage : "Default Message",
    trabscribeState : "close",
    opacity : 0.8,
    overlay : true
}
const mutations = {
    changeTranscribeState(state, status){
      if(status == "start"){
        state.overlay = true
      } else if(status == "close") {
        state.overlay = false
      }
      state.trabscribeState = status
    },
    changeMessage(state, message) {
      state.transcribe = message
    }
}
const actions= {
  start({ commit }) {
    // clearTimeout(number)
    commit('changeTranscribeState', "start");
    // number = setTimeout(() => commit('reset'), 2500);
  },
  listen ({ commit }) {
    commit('changeMessage', "listening Govajee command .....")
    commit('changeTranscribeState', "listen");
  },
  wait ({commit}) {
    commit('changeTranscribeState', "wait");
  },
  close ({ commit }) {
    commit('changeTranscribeState', "close");
  }
}

export default {
  namespaced: true,
  state,
  actions,
  mutations
}